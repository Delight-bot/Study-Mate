from .base_service import BaseLLMService
from typing import Dict, Any
import httpx
import os

class DeepSeekService(BaseLLMService):
    """Service for DeepSeek models"""

    def __init__(self, api_key: str = None, model: str = "deepseek-chat", temperature: float = 0.7, max_tokens: int = 1000):
        api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        super().__init__(api_key, model, temperature, max_tokens)
        self.base_url = "https://api.deepseek.com/v1"

    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using DeepSeek API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "response_text": data["choices"][0]["message"]["content"],
                        "token_count": data.get("usage", {}).get("total_tokens"),
                        "model": self.model,
                        "metadata": {
                            "finish_reason": data["choices"][0].get("finish_reason"),
                            "prompt_tokens": data.get("usage", {}).get("prompt_tokens"),
                            "completion_tokens": data.get("usage", {}).get("completion_tokens")
                        }
                    }
                else:
                    raise Exception(f"API request failed with status {response.status_code}")

        except Exception as e:
            return {
                "response_text": f"Error: {str(e)}",
                "token_count": 0,
                "model": self.model,
                "error": True,
                "metadata": {"error_message": str(e)}
            }
