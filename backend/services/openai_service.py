from .base_service import BaseLLMService
from typing import Dict, Any
import openai
import os

class OpenAIService(BaseLLMService):
    """Service for OpenAI GPT models"""

    def __init__(self, api_key: str = None, model: str = "gpt-4", temperature: float = 0.7, max_tokens: int = 1000):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        super().__init__(api_key, model, temperature, max_tokens)
        self.client = openai.AsyncOpenAI(api_key=self.api_key)

    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using OpenAI API"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful, knowledgeable assistant that provides clear and accurate answers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            return {
                "response_text": response.choices[0].message.content,
                "token_count": response.usage.total_tokens if response.usage else None,
                "model": self.model,
                "metadata": {
                    "finish_reason": response.choices[0].finish_reason,
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                    "completion_tokens": response.usage.completion_tokens if response.usage else None
                }
            }
        except Exception as e:
            return {
                "response_text": f"Error: {str(e)}",
                "token_count": 0,
                "model": self.model,
                "error": True,
                "metadata": {"error_message": str(e)}
            }
