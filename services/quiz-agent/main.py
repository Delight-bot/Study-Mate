import json
from typing import List, Optional

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel

from database import execute_query, execute_update, init_database
from llm_client import generate_quiz_questions

app = FastAPI(title="Quiz Agent")
router = APIRouter()


class GenerateQuizRequest(BaseModel):
    user_id: int
    subject: str
    source_text: str
    num_questions: int = 5
    difficulty: str = "medium"


class SubmitQuizRequest(BaseModel):
    user_id: int
    answers: List[int]


@app.on_event("startup")
async def startup():
    await init_database()


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "quiz-agent"}


@router.post("/generate")
async def generate_quiz(req: GenerateQuizRequest):
    try:
        questions = await generate_quiz_questions(
            req.subject, req.source_text, req.num_questions, req.difficulty
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM generation failed: {str(e)}")

    quiz_id = await execute_update(
        "INSERT INTO quizzes (user_id, subject, difficulty) VALUES (?, ?, ?)",
        (req.user_id, req.subject, req.difficulty),
    )

    question_ids = []
    for q in questions:
        qid = await execute_update(
            "INSERT INTO quiz_questions (quiz_id, question, choices, correct_index, explanation) "
            "VALUES (?, ?, ?, ?, ?)",
            (quiz_id, q["question"], json.dumps(q["choices"]), q["correct_index"], q.get("explanation", "")),
        )
        question_ids.append(qid)

    return {
        "quiz_id": quiz_id,
        "questions": [
            {
                "id": qid,
                "question": q["question"],
                "choices": q["choices"],
            }
            for qid, q in zip(question_ids, questions)
        ],
    }


@router.post("/{quiz_id}/submit")
async def submit_quiz(quiz_id: int, req: SubmitQuizRequest):
    rows = await execute_query(
        "SELECT id, correct_index, explanation FROM quiz_questions WHERE quiz_id = ? ORDER BY id",
        (quiz_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Quiz not found")

    if len(req.answers) != len(rows):
        raise HTTPException(
            status_code=400,
            detail=f"Expected {len(rows)} answers, got {len(req.answers)}",
        )

    score = 0
    feedback = []
    for row, answer in zip(rows, req.answers):
        correct = answer == row["correct_index"]
        if correct:
            score += 1
        feedback.append(
            {
                "question_id": row["id"],
                "correct": correct,
                "correct_index": row["correct_index"],
                "explanation": row["explanation"],
            }
        )

    await execute_update(
        "INSERT INTO quiz_attempts (quiz_id, user_id, score, total, answers) VALUES (?, ?, ?, ?, ?)",
        (quiz_id, req.user_id, score, len(rows), json.dumps(req.answers)),
    )

    return {"score": score, "total": len(rows), "feedback": feedback}


@router.get("/{user_id}/history")
async def quiz_history(user_id: int):
    rows = await execute_query(
        "SELECT id, quiz_id, score, total, created_at FROM quiz_attempts "
        "WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    )
    return [dict(row) for row in rows]


app.include_router(router, prefix="/api/quiz", tags=["quiz"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
