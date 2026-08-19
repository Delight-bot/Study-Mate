from fastapi import APIRouter, HTTPException
from typing import Optional
from services import (
    OpenAIService,
    ClaudeService,
    GeminiService,
    DeepSeekService,
    LlamaService
)

router = APIRouter()

# Initialize services
services = {
    "gpt": OpenAIService(),
    "claude": ClaudeService(),
    "gemini": GeminiService(),
    "deepseek": DeepSeekService(),
    "llama": LlamaService()
}

@router.post("/query/{llm_name}")
async def query_single_llm(
    llm_name: str,
    prompt: str,
    temperature: Optional[float] = 0.7,
    max_tokens: Optional[int] = 1000
):
    """Query a single LLM directly"""
    if llm_name not in services:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid LLM name. Must be one of: {', '.join(services.keys())}"
        )

    try:
        service = services[llm_name]
        service.temperature = temperature
        service.max_tokens = max_tokens

        result = await service.timed_generate(prompt)
        return {
            "llm": llm_name,
            "response": result.get("response_text"),
            "response_time": result.get("response_time"),
            "token_count": result.get("token_count"),
            "metadata": result.get("metadata", {})
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying {llm_name}: {str(e)}")

@router.get("/available")
async def get_available_llms():
    """Get list of available LLMs and their status"""
    status = {}

    for llm_name, service in services.items():
        try:
            # Check if API key is configured
            has_key = service.api_key is not None and service.api_key != ""
            status[llm_name] = {
                "available": has_key,
                "model": service.model,
                "status": "ready" if has_key else "missing_api_key"
            }
        except Exception as e:
            status[llm_name] = {
                "available": False,
                "status": "error",
                "error": str(e)
            }

    return status

@router.get("/models")
async def get_models_info():
    """Get information about all configured models"""
    return {
        "gpt": {
            "provider": "OpenAI",
            "default_model": "gpt-4",
            "alternatives": ["gpt-3.5-turbo", "gpt-4-turbo"]
        },
        "claude": {
            "provider": "Anthropic",
            "default_model": "claude-3-5-sonnet-20241022",
            "alternatives": ["claude-3-opus-20240229", "claude-3-haiku-20240307"]
        },
        "gemini": {
            "provider": "Google",
            "default_model": "gemini-2.5-flash",
            "alternatives": ["gemini-2.0-flash", "gemini-2.5-pro"]
        },
        "deepseek": {
            "provider": "DeepSeek",
            "default_model": "deepseek-chat",
            "alternatives": []
        },
        "llama": {
            "provider": "Meta (via Together AI)",
            "default_model": "meta-llama/Llama-2-70b-chat-hf",
            "alternatives": ["meta-llama/Llama-2-13b-chat-hf"]
        }
    }
