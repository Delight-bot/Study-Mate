import os
from typing import List

import openai
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

COLLECTION = "notes"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_SIZE = 1536
CHUNK_SIZE = 500

_client: AsyncQdrantClient | None = None


def get_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = AsyncQdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
    return _client


async def ensure_collection():
    client = get_client()
    exists = await client.collection_exists(COLLECTION)
    if not exists:
        await client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=EMBEDDING_SIZE, distance=Distance.COSINE),
        )


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    words = text.split()
    chunks = []
    current: List[str] = []
    current_len = 0
    for word in words:
        current.append(word)
        current_len += len(word) + 1
        if current_len >= chunk_size:
            chunks.append(" ".join(current))
            current, current_len = [], 0
    if current:
        chunks.append(" ".join(current))
    return chunks or [text]


async def embed_texts(texts: List[str]) -> List[List[float]]:
    client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = await client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


async def index_note(note_id: int, user_id: int, subject: str, content: str):
    await ensure_collection()
    chunks = chunk_text(content)
    vectors = await embed_texts(chunks)

    points = [
        PointStruct(
            id=note_id * 1000 + i,
            vector=vector,
            payload={
                "note_id": note_id,
                "user_id": user_id,
                "subject": subject,
                "chunk_text": chunk,
            },
        )
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]
    await get_client().upsert(collection_name=COLLECTION, points=points)


async def search_notes(user_id: int, query: str, limit: int = 5):
    await ensure_collection()
    query_vector = (await embed_texts([query]))[0]

    results = await get_client().query_points(
        collection_name=COLLECTION,
        query=query_vector,
        query_filter=Filter(
            must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
        ),
        limit=limit,
    )
    return [
        {
            "note_id": point.payload["note_id"],
            "chunk_text": point.payload["chunk_text"],
            "score": point.score,
        }
        for point in results.points
    ]
