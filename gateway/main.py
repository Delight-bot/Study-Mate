import os

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="StudeyMate Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LLM_ROUTER_URL = os.getenv("LLM_ROUTER_URL", "http://localhost:8000")
QUIZ_AGENT_URL = os.getenv("QUIZ_AGENT_URL", "http://localhost:8001")
FLASHCARD_AGENT_URL = os.getenv("FLASHCARD_AGENT_URL", "http://localhost:8002")
NOTES_AGENT_URL = os.getenv("NOTES_AGENT_URL", "http://localhost:8003")

# First path segment after /api/ -> upstream base URL. Each upstream mounts its
# own routes under the same /api/<segment> prefix, so the full path is forwarded unchanged.
ROUTES = {
    "chat": LLM_ROUTER_URL,
    "llm": LLM_ROUTER_URL,
    "score": LLM_ROUTER_URL,
    "profile": LLM_ROUTER_URL,
    "quiz": QUIZ_AGENT_URL,
    "flashcards": FLASHCARD_AGENT_URL,
    "notes": NOTES_AGENT_URL,
}

SERVICES = {
    "llm-router": LLM_ROUTER_URL,
    "quiz-agent": QUIZ_AGENT_URL,
    "flashcard-agent": FLASHCARD_AGENT_URL,
    "notes-agent": NOTES_AGENT_URL,
}

HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length",
}


@app.get("/health")
async def health():
    results = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, base_url in SERVICES.items():
            try:
                resp = await client.get(f"{base_url}/health")
                results[name] = resp.status_code == 200
            except httpx.HTTPError:
                results[name] = False
    return {"status": "healthy" if all(results.values()) else "degraded", "services": results}


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(path: str, request: Request):
    segment = path.split("/", 1)[0]
    base_url = ROUTES.get(segment)
    if base_url is None:
        return Response(content=f'{{"detail":"Unknown API route: /{segment}"}}', status_code=404,
                         media_type="application/json")

    target_url = f"{base_url}/api/{path}"
    body = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP_BY_HOP_HEADERS}

    async with httpx.AsyncClient(timeout=60.0) as client:
        upstream_response = await client.request(
            request.method,
            target_url,
            params=request.query_params,
            content=body,
            headers=headers,
        )

    response_headers = {
        k: v for k, v in upstream_response.headers.items() if k.lower() not in HOP_BY_HOP_HEADERS
    }
    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=response_headers,
        media_type=upstream_response.headers.get("content-type"),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
