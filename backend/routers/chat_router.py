import asyncio

from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from models import ChatRequest, ChatResponse, LLMResponse, WalkthroughRequest
from services import (
    OpenAIService,
    ClaudeService,
    GeminiService,
    DeepSeekService,
    LlamaService
)
from database import execute_query
from graph import build_ask_graph
from graph.ask_graph import LLM_TIMEOUT_SECONDS
import os

router = APIRouter()

# Initialize LLM services - only include those with valid API keys
def get_available_services():
    """Only initialize services that have API keys configured"""
    services = {}

    if os.getenv("OPENAI_API_KEY"):
        services["gpt"] = OpenAIService()

    if os.getenv("ANTHROPIC_API_KEY"):
        services["claude"] = ClaudeService()

    if os.getenv("GEMINI_API_KEY"):
        services["gemini"] = GeminiService()

    if os.getenv("DEEPSEEK_API_KEY"):
        services["deepseek"] = DeepSeekService()

    if os.getenv("LLAMA_API_KEY"):
        services["llama"] = LlamaService()

    return services

llm_services = get_available_services()

ask_graph = build_ask_graph(llm_services)

@router.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    Main endpoint for asking questions to all LLMs

    Runs the LangGraph pipeline in graph/ask_graph.py:
    1. Detects subject/difficulty and builds an optimized prompt per LLM
    2. Sends to all configured LLMs in parallel (each time-bounded)
    3. Stores successful answers
    4. Scores + cross-checks the answers and fuses the best sections
    """
    try:
        state = await ask_graph.ainvoke({
            "user_id": current_user["user_id"],
            "question": request.question,
            "subject": request.subject,
            "context": request.context,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

    # Parallel branches finish in completion order; keep a stable order.
    order = list(llm_services)
    responses = sorted(state.get("responses", []), key=lambda r: order.index(r["llm_name"]))

    return ChatResponse(
        question=request.question,
        responses=responses,
        subject=request.subject,
        detected_subject=state.get("detected_subject"),
        difficulty=state.get("difficulty"),
        evaluation=state.get("evaluation"),
        fused=state.get("fused"),
    )

@router.get("/history")
async def get_chat_history(limit: int = 20, subject: str = None, current_user: dict = Depends(get_current_user)):
    """Get the current user's chat history, optionally scoped to one subject/room"""
    user_id = current_user["user_id"]
    try:
        if subject:
            results = await execute_query(
                """SELECT DISTINCT r.question, r.subject_id, s.name as subject_name, r.created_at
                   FROM llm_responses r
                   JOIN subjects s ON r.subject_id = s.id
                   WHERE r.user_id = ? AND s.name = ?
                   ORDER BY r.created_at DESC
                   LIMIT ?""",
                (user_id, subject, limit)
            )
        else:
            results = await execute_query(
                """SELECT DISTINCT r.question, r.subject_id, s.name as subject_name, r.created_at
                   FROM llm_responses r
                   LEFT JOIN subjects s ON r.subject_id = s.id
                   WHERE r.user_id = ?
                   ORDER BY r.created_at DESC
                   LIMIT ?""",
                (user_id, limit)
            )
        return [dict(row) for row in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")


@router.get("/subjects")
async def list_subjects():
    """List available subjects/rooms to ask questions in"""
    try:
        results = await execute_query(
            "SELECT id, name, description FROM subjects ORDER BY name"
        )
        return [dict(row) for row in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching subjects: {str(e)}")


def _walkthrough_prompt(question: str, previous_answer: str, subject: str | None) -> str:
    parts = []
    if subject:
        parts.append(f"Subject: {subject}")
    parts.append(f"Original question: {question}")
    parts.append(f'Your previous answer:\n"""\n{previous_answer}\n"""')
    parts.append(
        "The student picked this answer as the most helpful one. Break it down into "
        "a clear, numbered, step-by-step walkthrough they can follow along with — one "
        "concrete step per number, in the order they should work through it. Keep each "
        "step focused and concise."
    )
    return "\n\n".join(parts)


@router.post("/walkthrough")
async def walkthrough(request: WalkthroughRequest, current_user: dict = Depends(get_current_user)):
    """Re-ask the chosen LLM to break its own answer into numbered steps."""
    service = llm_services.get(request.llm_name)
    if not service:
        raise HTTPException(status_code=400, detail=f"'{request.llm_name}' isn't a configured LLM")

    prompt = _walkthrough_prompt(request.question, request.previous_answer, request.subject)
    try:
        result = await asyncio.wait_for(service.timed_generate(prompt), timeout=LLM_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail=f"{request.llm_name} timed out after {LLM_TIMEOUT_SECONDS}s")

    if result.get("error"):
        raise HTTPException(status_code=502, detail=result.get("response_text", "Walkthrough generation failed"))

    return {
        "llm_name": request.llm_name,
        "steps_text": result.get("response_text", ""),
        "response_time": result.get("response_time", 0),
    }
