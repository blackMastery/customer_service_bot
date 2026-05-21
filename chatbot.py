import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from loguru import logger

from config import get_settings


class CustomerServiceBot:
    """Production-ready customer service chatbot using LangChain."""
    
    def __init__(self):
        self.settings = get_settings()
        self.llm = self._initialize_llm()
        self.embeddings = self._initialize_embeddings()
        self.vector_store = None
        self.conversation_chains: Dict[str, ConversationalRetrievalChain] = {}
        self.memories: Dict[str, ConversationBufferMemory] = {}
        
        # Initialize vector store if knowledge base exists
        try:
            self.vector_store = self._load_vector_store()
            logger.info("Vector store loaded successfully")
        except Exception as e:
            logger.warning("Vector store not loaded: {}", e)
    
    def _initialize_llm(self):
        """Initialize the language model based on configuration."""
        try:
            if self.settings.llm_provider == "openai":
                return ChatOpenAI(
                    model=self.settings.model_name,
                    temperature=self.settings.temperature,
                    max_tokens=self.settings.max_tokens,
                    api_key=self.settings.openai_api_key,
                )
            elif self.settings.llm_provider == "anthropic":
                return ChatAnthropic(
                    model=self.settings.model_name,
                    temperature=self.settings.temperature,
                    max_tokens=self.settings.max_tokens,
                    api_key=self.settings.anthropic_api_key
                )
            else:
                raise ValueError(f"Unsupported LLM provider: {self.settings.llm_provider}")
        except Exception as e:
            logger.error("Failed to initialize LLM: {}", e)
            raise
    
    def _initialize_embeddings(self):
        """Initialize embeddings model."""
        try:
            return OpenAIEmbeddings(
                model=self.settings.embeddings_model,
                api_key=self.settings.openai_api_key
            )
        except Exception as e:
            logger.error("Failed to initialize embeddings: {}", e)
            raise
    
    def _load_vector_store(self) -> Optional[Chroma]:
        """Load existing vector store for knowledge retrieval."""
        try:
            return Chroma(
                persist_directory=self.settings.vector_store_path,
                embedding_function=self.embeddings
            )
        except Exception as e:
            logger.warning("Could not load vector store: {}", e)
            return None
    
    def _get_combine_docs_prompt(self) -> PromptTemplate:
        """QA prompt for the stuff chain: only context/question/chat_history are runtime inputs.

        Company, hours, and support email are bound via partial_variables so they are not
        passed through chain memory (which requires a single user input key: question).
        """
        template = """You are a helpful and professional customer service representative for {company_name}.

Your responsibilities:
- Provide accurate, helpful information based on the context provided
- Be polite, empathetic, and professional at all times
- If you don't know the answer, admit it and offer to escalate to a human agent
- Keep responses concise but comprehensive
- Always maintain a positive and solution-oriented attitude

Official business hours (use when relevant): {business_hours}
Support email (use when relevant): {support_email}

Context from knowledge base:
{context}

Conversation history (condensed for this turn):
{chat_history}

Customer: {question}

Customer Service Rep:"""

        return PromptTemplate(
            template=template,
            input_variables=["context", "chat_history", "question"],
            partial_variables={
                "company_name": self.settings.company_name,
                "business_hours": self.settings.business_hours,
                "support_email": self.settings.support_email,
            },
        )
    
    def _get_or_create_memory(self, session_id: str) -> ConversationBufferMemory:
        """Get or create conversation memory for a session."""
        if session_id not in self.memories:
            self.memories[session_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )
            logger.info(f"Created new memory for session: {session_id}")
        return self.memories[session_id]
    
    def _get_or_create_chain(self, session_id: str) -> ConversationalRetrievalChain:
        """Get or create a conversational chain for a session."""
        if session_id not in self.conversation_chains:
            memory = self._get_or_create_memory(session_id)
            
            if self.vector_store:
                # With knowledge base — business fields on the QA prompt only (partial_variables)
                chain = ConversationalRetrievalChain.from_llm(
                    llm=self.llm,
                    retriever=self.vector_store.as_retriever(search_kwargs={"k": 3}),
                    memory=memory,
                    return_source_documents=True,
                    verbose=False,
                    combine_docs_chain_kwargs={
                        "prompt": self._get_combine_docs_prompt(),
                    },
                )
            else:
                # Without knowledge base - simple conversation
                from langchain.chains import ConversationChain
                chain = ConversationChain(
                    llm=self.llm,
                    memory=memory,
                    verbose=False
                )
            
            self.conversation_chains[session_id] = chain
            logger.info(f"Created new conversation chain for session: {session_id}")
        
        return self.conversation_chains[session_id]
    
    async def chat(
        self,
        message: str,
        session_id: str,
        metadata: Optional[Dict] = None
    ) -> Tuple[str, Optional[List[Dict]]]:
        """
        Process a chat message and return response.
        
        Args:
            message: User's message
            session_id: Unique session identifier
            metadata: Optional metadata (user_id, timestamp, etc.)
        
        Returns:
            Tuple of (response_text, source_documents)
        """
        try:
            logger.info(f"Processing message for session {session_id}: {message[:100]}...")
            
            # Get or create conversation chain
            chain = self._get_or_create_chain(session_id)
            
            # Prepare input with business context
            if self.vector_store:
                result = await asyncio.to_thread(
                    chain.invoke,
                    {"question": message},
                )
                
                response = result["answer"]
                sources = result.get("source_documents", [])
                source_info = [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc in sources
                ] if sources else None
            else:
                result = await asyncio.to_thread(chain.predict, input=message)
                response = result
                source_info = None
            
            logger.info(f"Generated response for session {session_id}")
            return response, source_info
            
        except Exception as e:
            logger.opt(exception=True).error("Error processing chat message: {}", e)
            return self._get_error_response(), None
    
    def _get_error_response(self) -> str:
        """Return a user-friendly error message."""
        return (
            f"I apologize, but I'm experiencing technical difficulties. "
            f"Please try again in a moment, or contact our support team at "
            f"{self.settings.support_email} for immediate assistance."
        )
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieve conversation history for a session."""
        if session_id not in self.memories:
            return []
        
        memory = self.memories[session_id]
        messages = memory.chat_memory.messages
        
        history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
        
        return history
    
    def clear_conversation(self, session_id: str) -> bool:
        """Clear conversation history for a session."""
        try:
            if session_id in self.memories:
                self.memories[session_id].clear()
                logger.info(f"Cleared conversation history for session: {session_id}")
            if session_id in self.conversation_chains:
                del self.conversation_chains[session_id]
            return True
        except Exception as e:
            logger.error("Error clearing conversation: {}", e)
            return False
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old inactive sessions to free memory."""
        # This is a simplified version - in production, track session timestamps
        current_sessions = len(self.memories)
        if current_sessions > 100:  # Arbitrary threshold
            logger.warning(f"High number of sessions: {current_sessions}. Consider implementing TTL.")


# Global bot instance
_bot_instance: Optional[CustomerServiceBot] = None


def get_bot() -> CustomerServiceBot:
    """Get or create the global bot instance."""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = CustomerServiceBot()
    return _bot_instance
