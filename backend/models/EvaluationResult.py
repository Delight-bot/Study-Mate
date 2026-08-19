from pydantic import BaseModel, Field
from typing import Optional

class EvaluationResult(BaseModel):
    """Model for evaluation scores"""
    response_id: int
    clarity_score: float = Field(..., ge=0.0, le=1.0)
    depth_score: float = Field(..., ge=0.0, le=1.0)
    formatting_score: float = Field(..., ge=0.0, le=1.0)
    correctness_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    overall_score: float = Field(..., ge=0.0, le=1.0)

class DifficultyScore(BaseModel):
    """Model for question difficulty assessment"""
    question: str
    subject_id: Optional[int] = None
    difficulty_level: str = Field(..., description="easy, medium, or hard")
    difficulty_score: float = Field(..., ge=0.0, le=1.0)
    keyword_complexity: float = Field(..., ge=0.0, le=1.0)
    avg_response_time: Optional[float] = None

class HallucinationCheck(BaseModel):
    """Model for hallucination detection results"""
    llm_name: str
    question: str
    response_text: str
    inconsistency_score: float = Field(..., ge=0.0, le=1.0)
    conflicting_llms: list[str] = []
    flagged_content: Optional[str] = None
    is_hallucination: bool = False
