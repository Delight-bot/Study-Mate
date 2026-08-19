from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LLMResponse(BaseModel):
    """Model for LLM response data"""
    id: Optional[int] = None
    user_id: int
    question: str
    subject_id: Optional[int] = None
    llm_name: str = Field(..., description="Name of the LLM (gpt, claude, gemini, deepseek, llama)")
    response_text: str
    response_time: float = Field(..., description="Response time in seconds")
    token_count: Optional[int] = None
    prompt_used: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class LLMConfig(BaseModel):
    """Configuration for LLM service"""
    name: str
    model: str
    api_key: str
    temperature: float = 0.7
    max_tokens: int = 1000
    enabled: bool = True

class MultiLLMResponse(BaseModel):
    """Response from multiple LLMs"""
    question: str
    subject: Optional[str] = None
    responses: list[LLMResponse]
    best_llm: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
