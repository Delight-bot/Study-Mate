from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from models import ChatRequest, ChatResponse, LLMResponse
from services import (
    OpenAIService,
    ClaudeService,
    GeminiService,
    DeepSeekService,
    LlamaService
)
from database import execute_query
from graph import build_ask_graph
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
