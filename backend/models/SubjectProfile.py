from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SubjectProfile(BaseModel):
    """Model for user's performance profile per subject"""
    id: Optional[int] = None
    user_id: int
    subject_id: int
    subject_name: Optional[str] = None
    best_llm: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    wins_gpt: int = 0
    wins_claude: int = 0
    wins_gemini: int = 0
    wins_deepseek: int = 0
    wins_llama: int = 0
    total_questions: int = 0
    last_updated: datetime = Field(default_factory=datetime.now)

    def get_win_rate(self, llm_name: str) -> float:
        """Calculate win rate for a specific LLM"""
        if self.total_questions == 0:
            return 0.0
        wins = getattr(self, f"wins_{llm_name}", 0)
        return wins / self.total_questions

    def update_wins(self, llm_name: str):
        """Increment win count for an LLM"""
        attr_name = f"wins_{llm_name}"
        if hasattr(self, attr_name):
            current = getattr(self, attr_name)
            setattr(self, attr_name, current + 1)
        self.total_questions += 1
        self.last_updated = datetime.now()

class ProfileSummary(BaseModel):
    """Summary of user's LLM preferences across all subjects"""
    user_id: int
    profiles: list[SubjectProfile]
    overall_best_llm: str
    total_interactions: int
