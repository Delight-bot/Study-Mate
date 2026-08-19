from datetime import datetime, timezone

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel

from database import execute_query, execute_update, init_database
from llm_client import generate_flashcards
from sm2 import schedule

app = FastAPI(title="Flashcard Agent")
router = APIRouter()


class GenerateFlashcardsRequest(BaseModel):
    user_id: int
    subject: str
    source_text: str
    count: int = 10


class ReviewRequest(BaseModel):
    quality: int  # 0-5


@app.on_event("startup")
async def startup():
    await init_database()


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "flashcard-agent"}


@router.post("/generate")
async def generate(req: GenerateFlashcardsRequest):
    try:
        cards = await generate_flashcards(req.subject, req.source_text, req.count)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM generation failed: {str(e)}")

    now = datetime.now(timezone.utc)
    created = []
    for card in cards:
        card_id = await execute_update(
            "INSERT INTO flashcards (user_id, subject, front, back, next_review_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (req.user_id, req.subject, card["front"], card["back"], now),
        )
        created.append({"id": card_id, "front": card["front"], "back": card["back"]})

    return {"flashcards": created}


@router.get("/{user_id}")
async def due_flashcards(user_id: int, subject: str | None = None):
    now = datetime.now(timezone.utc)
    if subject:
        rows = await execute_query(
            "SELECT * FROM flashcards WHERE user_id = ? AND subject = ? AND next_review_at <= ? "
            "ORDER BY next_review_at",
            (user_id, subject, now),
        )
    else:
        rows = await execute_query(
            "SELECT * FROM flashcards WHERE user_id = ? AND next_review_at <= ? ORDER BY next_review_at",
            (user_id, now),
        )
    return [dict(row) for row in rows]


@router.post("/{card_id}/review")
async def review(card_id: int, req: ReviewRequest):
    if not 0 <= req.quality <= 5:
        raise HTTPException(status_code=400, detail="quality must be between 0 and 5")

    rows = await execute_query("SELECT * FROM flashcards WHERE id = ?", (card_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    card = rows[0]

    result = schedule(req.quality, card["interval"], card["ease_factor"], card["repetitions"])

    await execute_update(
        "UPDATE flashcards SET interval = ?, ease_factor = ?, repetitions = ?, next_review_at = ? "
        "WHERE id = ?",
        (result["interval"], result["ease_factor"], result["repetitions"], result["next_review_at"], card_id),
    )
    await execute_update(
        "INSERT INTO flashcard_reviews (flashcard_id, quality) VALUES (?, ?)",
        (card_id, req.quality),
    )

    return {"card_id": card_id, **result}


app.include_router(router, prefix="/api/flashcards", tags=["flashcards"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
