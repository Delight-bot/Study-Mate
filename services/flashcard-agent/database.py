import asyncio
import os
from pathlib import Path

import asyncpg

_pool: asyncpg.Pool | None = None


def _dsn() -> str:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "studeymate")
    password = os.getenv("POSTGRES_PASSWORD", "")
    db = os.getenv("POSTGRES_DB", "flashcard_agent")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


async def _get_pool(retries: int = 10, delay: float = 2.0) -> asyncpg.Pool:
    global _pool
    if _pool is None:
        for attempt in range(1, retries + 1):
            try:
                _pool = await asyncpg.create_pool(dsn=_dsn(), min_size=1, max_size=5)
                break
            except (OSError, asyncpg.PostgresError) as e:
                if attempt == retries:
                    raise
                print(f"Postgres not ready yet ({e}), retrying {attempt}/{retries}...")
                await asyncio.sleep(delay)
    return _pool


def _to_positional(query: str) -> str:
    """Rewrite sqlite-style '?' placeholders to asyncpg-style '$1, $2, ...'."""
    count = 0
    out = []
    for ch in query:
        if ch == "?":
            count += 1
            out.append(f"${count}")
        else:
            out.append(ch)
    return "".join(out)


async def init_database():
    schema_path = Path(__file__).parent / "schema.sql"
    pool = await _get_pool()
    async with pool.acquire() as conn:
        with open(schema_path, "r") as f:
            schema = f.read()
        await conn.execute(schema)


async def execute_query(query: str, params: tuple = ()):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(_to_positional(query), *params)


async def execute_update(query: str, params: tuple = ()):
    """INSERTs auto-return the new row's id; other statements return None."""
    pool = await _get_pool()
    q = _to_positional(query)
    stripped = q.strip().upper()
    async with pool.acquire() as conn:
        if stripped.startswith("INSERT"):
            if "RETURNING" not in stripped:
                q = q.rstrip().rstrip(";") + " RETURNING id"
            return await conn.fetchval(q, *params)
        await conn.execute(q, *params)
        return None
