import streamlit as st
import uuid
import asyncio
from datetime import datetime
from typing import List, Dict
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot import get_bot
from config import get_settings


# Page config
st.set_page_config(
    page_title="Customer Service Chatbot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
    .sidebar-info {
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "bot" not in st.session_state:
        with st.spinner("Initializing chatbot..."):
            st.session_state.bot = get_bot()
    
    if "settings" not in st.session_state:
        st.session_state.settings = get_settings()


async def send_message(message: str):
    """Send a message to the bot and get response."""
    try:
        response, sources = await st.session_state.bot.chat(
            message=message,
            session_id=st.session_state.session_id,
            metadata={"timestamp": datetime.utcnow().isoformat()}
        )
        return response, sources
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None, None


def display_message(role: str, content: str, sources: List[Dict] = None):
    """Display a chat message with custom styling."""
    with st.chat_message(role):
        st.markdown(content)
        
        # Display sources if available
        if sources and role == "assistant":
            with st.expander("📚 View Sources"):
                for i, source in enumerate(sources, 1):
                    st.markdown(f"**Source {i}:**")
                    st.text(source.get("content", "")[:200] + "...")
                    if source.get("metadata"):
                        st.json(source["metadata"])


def main():
    """Main application."""
    initialize_session_state()
    settings = st.session_state.settings
    
    # Sidebar
    with st.sidebar:
        st.title("💬 Customer Service Bot")
        st.markdown("---")
        
        # Company Info
        st.markdown('<div class="sidebar-info">', unsafe_allow_html=True)
        st.markdown(f"**Company:** {settings.company_name}")
        st.markdown(f"**Hours:** {settings.business_hours}")
        st.markdown(f"**Email:** {settings.support_email}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Session Info
        st.markdown("### Session Info")
        st.markdown(f"**Session ID:**")
        st.code(st.session_state.session_id[:8] + "...", language=None)
        st.markdown(f"**Messages:** {len(st.session_state.messages)}")
        
        # Controls
        st.markdown("---")
        st.markdown("### Controls")
        
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.bot.clear_conversation(st.session_state.session_id)
            st.session_state.messages = []
            st.rerun()
        
        if st.button("🔄 New Session", use_container_width=True):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()
        
        # Settings
        st.markdown("---")
        st.markdown("### Settings")
        
        with st.expander("⚙️ Configuration"):
            st.markdown(f"**LLM Provider:** {settings.llm_provider}")
            st.markdown(f"**Model:** {settings.model_name}")
            st.markdown(f"**Temperature:** {settings.temperature}")
            st.markdown(f"**Max Tokens:** {settings.max_tokens}")
        
        # Export Conversation
        if st.session_state.messages:
            st.markdown("---")
            if st.button("💾 Export Conversation", use_container_width=True):
                conversation_text = "\n\n".join([
                    f"{msg['role'].upper()}: {msg['content']}"
                    for msg in st.session_state.messages
                ])
                st.download_button(
                    label="Download as TXT",
                    data=conversation_text,
                    file_name=f"conversation_{st.session_state.session_id[:8]}.txt",
                    mime="text/plain"
                )
    
    # Main chat area
    st.title("Customer Service Assistant")
    st.markdown("Ask me anything about our products, services, or policies!")
    
    # Display chat history
    for message in st.session_state.messages:
        display_message(
            message["role"],
            message["content"],
            message.get("sources")
        )
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.utcnow()
        })
        display_message("user", prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, sources = asyncio.run(send_message(prompt))
                
                if response:
                    st.markdown(response)
                    
                    # Display sources if available
                    if sources:
                        with st.expander("📚 View Sources"):
                            for i, source in enumerate(sources, 1):
                                st.markdown(f"**Source {i}:**")
                                st.text(source.get("content", "")[:200] + "...")
                                if source.get("metadata"):
                                    st.json(source["metadata"])
                    
                    # Add assistant message to chat
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "sources": sources,
                        "timestamp": datetime.utcnow()
                    })
    
    # Quick action buttons
    st.markdown("---")
    st.markdown("### Quick Questions")
    col1, col2, col3 = st.columns(3)
    
    quick_questions = [
        "What are your business hours?",
        "How can I track my order?",
        "What is your return policy?"
    ]
    
    for col, question in zip([col1, col2, col3], quick_questions):
        with col:
            if st.button(question, use_container_width=True):
                # Simulate sending the question
                st.session_state.messages.append({
                    "role": "user",
                    "content": question,
                    "timestamp": datetime.utcnow()
                })
                st.rerun()


if __name__ == "__main__":
    main()
