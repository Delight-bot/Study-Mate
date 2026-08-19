from typing import Optional

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel

from database import execute_query, execute_update, init_database
from vector_store import get_client, index_note, search_notes

app = FastAPI(title="Notes Agent")
router = APIRouter()


class CreateNoteRequest(BaseModel):
    user_id: int
    subject: str
    title: str
    content: str


@app.on_event("startup")
async def startup():
    await init_database()


@app.get("/health")
async def health():
    qdrant_ok = True
    try:
        await get_client().get_collections()
    except Exception:
        qdrant_ok = False
    return {"status": "healthy", "service": "notes-agent", "qdrant": qdrant_ok}


@router.post("")
async def create_note(req: CreateNoteRequest):
    note_id = await execute_update(
        "INSERT INTO notes (user_id, subject, title, content) VALUES (?, ?, ?, ?)",
        (req.user_id, req.subject, req.title, req.content),
    )

    try:
        await index_note(note_id, req.user_id, req.subject, req.content)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Embedding/index failed: {str(e)}")

    return {"id": note_id, "user_id": req.user_id, "subject": req.subject, "title": req.title}


@router.get("/{user_id}")
async def list_notes(user_id: int):
    rows = await execute_query(
        "SELECT id, subject, title, content, created_at FROM notes WHERE user_id = ? "
        "ORDER BY created_at DESC",
        (user_id,),
    )
    return [dict(row) for row in rows]


@router.get("/{user_id}/search")
async def search(user_id: int, q: str):
    try:
        matches = await search_notes(user_id, q)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Search failed: {str(e)}")

    note_ids = {m["note_id"] for m in matches}
    notes_by_id = {}
    if note_ids:
        placeholders = ",".join("?" for _ in note_ids)
        rows = await execute_query(
            f"SELECT id, title, subject FROM notes WHERE id IN ({placeholders})",
            tuple(note_ids),
        )
        notes_by_id = {row["id"]: dict(row) for row in rows}

    return [
        {
            "note_id": m["note_id"],
            "score": m["score"],
            "chunk_text": m["chunk_text"],
            "note": notes_by_id.get(m["note_id"]),
        }
        for m in matches
    ]


app.include_router(router, prefix="/api/notes", tags=["notes"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
