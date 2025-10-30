import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from main import app
from chatbot import CustomerServiceBot
from config import get_settings


@pytest.fixture
def test_client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    bot = Mock(spec=CustomerServiceBot)
    bot.chat = AsyncMock(return_value=("Test response", None))
    bot.get_conversation_history = Mock(return_value=[])
    bot.clear_conversation = Mock(return_value=True)
    return bot


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, test_client):
        """Test health check returns 200."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data


class TestChatEndpoint:
    """Test chat endpoint."""
    
    @patch("main.get_bot")
    def test_chat_success(self, mock_get_bot, test_client, mock_bot):
        """Test successful chat request."""
        mock_get_bot.return_value = mock_bot
        
        payload = {
            "message": "What are your business hours?",
            "session_id": "test-session-123"
        }
        
        response = test_client.post("/chat", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        assert data["session_id"] == "test-session-123"
    
    @patch("main.get_bot")
    def test_chat_auto_session_id(self, mock_get_bot, test_client, mock_bot):
        """Test chat request without session_id generates one."""
        mock_get_bot.return_value = mock_bot
        
        payload = {"message": "Hello"}
        
        response = test_client.post("/chat", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) > 0
    
    def test_chat_empty_message(self, test_client):
        """Test chat with empty message fails validation."""
        payload = {"message": ""}
        
        response = test_client.post("/chat", json=payload)
        assert response.status_code == 422  # Validation error


class TestConversationEndpoints:
    """Test conversation management endpoints."""
    
    @patch("main.get_bot")
    def test_get_conversation(self, mock_get_bot, test_client, mock_bot):
        """Test getting conversation history."""
        mock_get_bot.return_value = mock_bot
        mock_bot.get_conversation_history.return_value = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        response = test_client.get("/conversation/test-session-123")
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == "test-session-123"
        assert len(data["messages"]) == 2
        assert data["message_count"] == 2
    
    @patch("main.get_bot")
    def test_clear_conversation(self, mock_get_bot, test_client, mock_bot):
        """Test clearing conversation."""
        mock_get_bot.return_value = mock_bot
        
        response = test_client.delete("/conversation/test-session-123")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert data["session_id"] == "test-session-123"


class TestChatbot:
    """Test chatbot functionality."""
    
    @pytest.mark.asyncio
    async def test_bot_initialization(self):
        """Test bot initializes correctly."""
        settings = get_settings()
        
        # This would require actual API keys, so we'll mock it
        with patch("chatbot.ChatOpenAI"), \
             patch("chatbot.OpenAIEmbeddings"):
            bot = CustomerServiceBot()
            assert bot is not None
            assert bot.settings is not None
    
    @pytest.mark.asyncio
    async def test_chat_creates_session(self):
        """Test that chat creates a session."""
        with patch("chatbot.ChatOpenAI"), \
             patch("chatbot.OpenAIEmbeddings"):
            bot = CustomerServiceBot()
            
            # Mock the actual chain call
            with patch.object(bot, '_get_or_create_chain') as mock_chain:
                mock_chain_instance = Mock()
                mock_chain_instance.__call__ = Mock(return_value={
                    "answer": "Test response"
                })
                mock_chain.return_value = mock_chain_instance
                
                response, sources = await bot.chat(
                    message="Test message",
                    session_id="test-123"
                )
                
                assert response is not None
                assert "test-123" in bot.memories


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    @patch("main.get_bot")
    def test_rate_limit_not_exceeded(self, mock_get_bot, test_client, mock_bot):
        """Test requests under rate limit succeed."""
        mock_get_bot.return_value = mock_bot
        
        payload = {"message": "Test"}
        
        # Make a few requests (under limit)
        for _ in range(3):
            response = test_client.post("/chat", json=payload)
            assert response.status_code == 200


class TestConfiguration:
    """Test configuration management."""
    
    def test_settings_load(self):
        """Test settings load correctly."""
        settings = get_settings()
        assert settings is not None
        assert settings.api_title is not None
        assert settings.company_name is not None
    
    def test_settings_defaults(self):
        """Test default settings."""
        settings = get_settings()
        assert settings.temperature == 0.7
        assert settings.max_tokens == 1000
        assert settings.max_conversation_history == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
