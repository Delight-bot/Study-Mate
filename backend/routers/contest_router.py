import random
import string
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from database import execute_query, execute_update

router = APIRouter()

CODE_ALPHABET = string.ascii_uppercase + string.digits


class CreateDuelRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=40)
    quiz_id: Optional[int] = None


class JoinDuelRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=40)


class ProgressRequest(BaseModel):
    participant_id: int
    focus_seconds: int = Field(..., ge=0)


class QuizResultRequest(BaseModel):
    participant_id: int
    score: int = Field(..., ge=0)
    total: int = Field(..., ge=0)


async def _generate_unique_code() -> str:
    for _ in range(10):
        code = ''.join(random.choices(CODE_ALPHABET, k=5))
        existing = await execute_query("SELECT id FROM study_duels WHERE code = ?", (code,))
        if not existing:
            return code
    raise HTTPException(status_code=500, detail="Could not generate a unique duel code")


async def _get_duel(code: str):
    result = await execute_query("SELECT id, code, quiz_id FROM study_duels WHERE code = ?", (code.upper(),))
    if not result:
        raise HTTPException(status_code=404, detail="Duel not found")
    return dict(result[0])


@router.post("/create")
async def create_duel(req: CreateDuelRequest):
    code = await _generate_unique_code()
    duel_id = await execute_update(
        "INSERT INTO study_duels (code, quiz_id) VALUES (?, ?)",
        (code, req.quiz_id)
    )
    participant_id = await execute_update(
        "INSERT INTO duel_participants (duel_id, display_name) VALUES (?, ?)",
        (duel_id, req.display_name)
    )
    return {"code": code, "participant_id": participant_id, "quiz_id": req.quiz_id}


@router.post("/{code}/join")
async def join_duel(code: str, req: JoinDuelRequest):
    duel = await _get_duel(code)
    participant_id = await execute_update(
        "INSERT INTO duel_participants (duel_id, display_name) VALUES (?, ?)",
        (duel["id"], req.display_name)
    )
    return {"code": duel["code"], "participant_id": participant_id, "quiz_id": duel["quiz_id"]}


@router.post("/{code}/progress")
async def update_progress(code: str, req: ProgressRequest):
    duel = await _get_duel(code)
    await execute_update(
        """UPDATE duel_participants
           SET focus_seconds = ?, last_active_at = CURRENT_TIMESTAMP
           WHERE id = ? AND duel_id = ?""",
        (req.focus_seconds, req.participant_id, duel["id"])
    )
    return {"ok": True}


@router.post("/{code}/quiz-result")
async def submit_quiz_result(code: str, req: QuizResultRequest):
    duel = await _get_duel(code)
    await execute_update(
        """UPDATE duel_participants
           SET quiz_score = ?, quiz_total = ?, last_active_at = CURRENT_TIMESTAMP
           WHERE id = ? AND duel_id = ?""",
        (req.score, req.total, req.participant_id, duel["id"])
    )
    return {"ok": True}


@router.get("/{code}")
async def get_duel(code: str):
    duel = await _get_duel(code)
    participants = await execute_query(
        """SELECT id, display_name, focus_seconds, quiz_score, quiz_total, last_active_at
           FROM duel_participants
           WHERE duel_id = ?
           ORDER BY focus_seconds DESC""",
        (duel["id"],)
    )
    return {
        "code": duel["code"],
        "quiz_id": duel["quiz_id"],
        "participants": [dict(p) for p in participants],
    }
