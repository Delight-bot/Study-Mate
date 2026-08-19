from pydantic import BaseModel, Field
from typing import Optional, Dict

class UserPreference(BaseModel):
    """Model for user preferences and metadata"""
    user_id: int
    preferred_style: Optional[str] = None  # 'detailed', 'concise', 'examples-heavy'
    preferred_format: Optional[str] = None  # 'bullet-points', 'paragraphs', 'code-focused'
    avoid_jargon: bool = False
    include_examples: bool = True
    explanation_depth: str = 'medium'  # 'basic', 'medium', 'advanced'

class UserChoice(BaseModel):
    """Model for user's choice of best response"""
    user_id: int
    question: str
    subject_id: Optional[int] = None
    chosen_llm: str
    all_response_ids: list[int]
    feedback: Optional[str] = None
    metadata: Optional[Dict] = None  # Additional refinement info

class UserFeedback(BaseModel):
    """Model for collecting user feedback on responses"""
    response_id: int
    rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = None
    helpful: bool = True
    needs_improvement: Optional[list[str]] = None
