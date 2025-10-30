from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import uuid
from loguru import logger

from config import get_settings
from chatbot import get_bot, CustomerServiceBot


# Pydantic models for API
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    metadata: Optional[Dict] = Field(None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What are your business hours?",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user_123"
            }
        }


class ChatResponse(BaseModel):
    response: str = Field(..., description="Bot's response")
    session_id: str = Field(..., description="Session ID for this conversation")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sources: Optional[List[Dict]] = Field(None, description="Source documents used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Our business hours are Monday-Friday, 9 AM - 5 PM EST.",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-01-15T10:30:00Z",
                "sources": None
            }
        }


class ConversationHistory(BaseModel):
    session_id: str
    messages: List[Dict[str, str]]
    message_count: int


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str


# Initialize FastAPI app
settings = get_settings()

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Production-ready customer service chatbot API"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate limiting middleware (simplified - use Redis in production)
request_counts: Dict[str, List[datetime]] = {}


async def check_rate_limit(request: Request):
    """Simple rate limiting check."""
    if not settings.rate_limit_enabled:
        return
    
    client_ip = request.client.host
    now = datetime.utcnow()
    
    if client_ip not in request_counts:
        request_counts[client_ip] = []
    
    # Remove old requests (older than 1 minute)
    request_counts[client_ip] = [
        ts for ts in request_counts[client_ip]
        if (now - ts).seconds < 60
    ]
    
    # Check limit
    if len(request_counts[client_ip]) >= settings.max_requests_per_minute:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    request_counts[client_ip].append(now)


# API Key authentication (optional)
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key if authentication is required."""
    if not settings.require_api_key:
        return True
    
    if not x_api_key or x_api_key not in settings.valid_api_keys:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
    return True


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal error occurred. Please try again later.",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.api_version
    )


# Main chat endpoint
@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    request: ChatRequest,
    _: bool = Depends(check_rate_limit),
    __: bool = Depends(verify_api_key),
    bot: CustomerServiceBot = Depends(get_bot)
):
    """
    Send a message to the chatbot and receive a response.
    
    - **message**: The user's message
    - **session_id**: Optional session ID for conversation continuity (auto-generated if not provided)
    - **user_id**: Optional user identifier for tracking
    - **metadata**: Optional additional metadata
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(f"Chat request - Session: {session_id}, User: {request.user_id}")
        
        # Process the message
        response, sources = await bot.chat(
            message=request.message,
            session_id=session_id,
            metadata={
                "user_id": request.user_id,
                **(request.metadata or {})
            }
        )
        
        return ChatResponse(
            response=response,
            session_id=session_id,
            sources=sources
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to process your message. Please try again."
        )


# Get conversation history
@app.get("/conversation/{session_id}", response_model=ConversationHistory, tags=["Chat"])
async def get_conversation(
    session_id: str,
    __: bool = Depends(verify_api_key),
    bot: CustomerServiceBot = Depends(get_bot)
):
    """Retrieve conversation history for a specific session."""
    try:
        history = bot.get_conversation_history(session_id)
        
        return ConversationHistory(
            session_id=session_id,
            messages=history,
            message_count=len(history)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve conversation history"
        )


# Clear conversation
@app.delete("/conversation/{session_id}", tags=["Chat"])
async def clear_conversation(
    session_id: str,
    __: bool = Depends(verify_api_key),
    bot: CustomerServiceBot = Depends(get_bot)
):
    """Clear conversation history for a specific session."""
    try:
        success = bot.clear_conversation(session_id)
        
        if success:
            return {"message": "Conversation cleared successfully", "session_id": session_id}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to clear conversation"
        )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")
    # Initialize the bot
    _ = get_bot()
    logger.info("Chatbot initialized successfully")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down application")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower()
    )
