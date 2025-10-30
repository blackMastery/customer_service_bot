import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    api_title: str = "Customer Service Chatbot API"
    api_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # LLM Configuration
    llm_provider: str = "openai"  # Options: openai, anthropic
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    model_name: str = "gpt-4-turbo-preview"  # or claude-3-sonnet-20240229
    temperature: float = 0.7
    max_tokens: int = 1000
    
    # Vector Store Configuration
    embeddings_model: str = "text-embedding-3-small"
    vector_store_path: str = "./data/vectorstore"
    knowledge_base_path: str = "./data/knowledge_base"
    
    # Conversation Configuration
    max_conversation_history: int = 10
    conversation_memory_type: str = "buffer"  # Options: buffer, summary, window
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    max_requests_per_minute: int = 60
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    
    # Security
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8501"]
    api_key_header: str = "X-API-Key"
    require_api_key: bool = False
    valid_api_keys: list[str] = []
    
    # Database (optional)
    database_url: Optional[str] = "sqlite:///./data/conversations.db"
    
    # Business Configuration
    company_name: str = "Your Company"
    support_email: str = "support@yourcompany.com"
    business_hours: str = "Monday-Friday, 9 AM - 5 PM EST"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
