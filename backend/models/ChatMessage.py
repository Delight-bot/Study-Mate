from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ChatMessage(BaseModel):
    """Model for incoming chat messages"""
    user_id: int
    message: str = Field(..., min_length=1, description="User's question or prompt")
    subject: Optional[str] = None
    context: Optional[str] = None

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    question: str = Field(..., min_length=1)
    subject: Optional[str] = None
    use_profiling: bool = True
    metadata: Optional[dict] = None

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    question: str
    responses: list[dict]  # List of LLM responses
    subject: Optional[str] = None
    detected_subject: Optional[str] = None  # set when no room subject was given
    difficulty: Optional[str] = None  # easy | medium | hard
    evaluation: Optional[dict] = None  # scores, ranking, cross-model consistency
    fused: Optional[dict] = None  # best-sections answer stitched from 2+ LLMs
    timestamp: datetime = Field(default_factory=datetime.now)
