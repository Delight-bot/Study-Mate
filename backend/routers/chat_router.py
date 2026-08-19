from fastapi import APIRouter, HTTPException
from typing import List
import asyncio
from models import ChatRequest, ChatResponse, LLMResponse
from services import (
    OpenAIService,
    ClaudeService,
    GeminiService,
    DeepSeekService,
    LlamaService,
    PromptOptimizer
)
from database import execute_query, execute_update
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

prompt_optimizer = PromptOptimizer()

@router.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    """
    Main endpoint for asking questions to all LLMs

    This endpoint:
    1. Takes a user question
    2. Optionally uses profiling to optimize prompts
    3. Sends to all 5 LLMs in parallel
    4. Returns all responses for user to choose
    """
    try:
        # Get subject ID if subject is provided
        subject_id = None
        if request.subject:
            result = await execute_query(
                "SELECT id FROM subjects WHERE name = ?",
                (request.subject,)
            )
            if result:
                subject_id = result[0]['id']

        # Get user profile for this subject (if profiling is enabled)
        profile = None
        if request.use_profiling and subject_id:
            profile_result = await execute_query(
                "SELECT * FROM profiles WHERE user_id = ? AND subject_id = ?",
                (request.user_id, subject_id)
            )
            if profile_result:
                profile = dict(profile_result[0])

        # Generate optimized prompts for each LLM
        prompts = {}
        for llm_name in llm_services.keys():
            prompts[llm_name] = prompt_optimizer.optimize_prompt(
                question=request.question,
                llm_name=llm_name,
                subject=request.subject
            )

        # Call all LLMs in parallel
        tasks = []
        for llm_name, service in llm_services.items():
            tasks.append(service.timed_generate(prompts[llm_name]))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and store in database
        responses = []
        for (llm_name, service), result in zip(llm_services.items(), results):
            if isinstance(result, Exception):
                response_data = {
                    "llm_name": llm_name,
                    "response_text": f"Error: {str(result)}",
                    "response_time": 0,
                    "error": True
                }
            else:
                response_data = {
                    "llm_name": llm_name,
                    "response_text": result.get("response_text", ""),
                    "response_time": result.get("response_time", 0),
                    "token_count": result.get("token_count"),
                    "model": result.get("model")
                }

                # Store response in database
                await execute_update(
                    """INSERT INTO llm_responses
                       (user_id, question, subject_id, llm_name, response_text, response_time, token_count, prompt_used)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        request.user_id,
                        request.question,
                        subject_id,
                        llm_name,
                        result.get("response_text", ""),
                        result.get("response_time", 0),
                        result.get("token_count"),
                        prompts[llm_name]
                    )
                )

            responses.append(response_data)

        return ChatResponse(
            question=request.question,
            responses=responses,
            subject=request.subject
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.get("/history/{user_id}")
async def get_chat_history(user_id: int, limit: int = 20):
    """Get chat history for a user"""
    try:
        results = await execute_query(
            """SELECT DISTINCT question, subject_id, created_at
               FROM llm_responses
               WHERE user_id = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (user_id, limit)
        )
        return [dict(row) for row in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")
