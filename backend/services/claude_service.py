from .base_service import BaseLLMService
from typing import Dict, Any
import anthropic
import os

class ClaudeService(BaseLLMService):
    """Service for Anthropic Claude models"""

    def __init__(self, api_key: str = None, model: str = "claude-3-5-sonnet-20241022", temperature: float = 0.7, max_tokens: int = 1000):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        super().__init__(api_key, model, temperature, max_tokens)
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)

    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using Anthropic Claude API"""
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return {
                "response_text": response.content[0].text,
                "token_count": response.usage.input_tokens + response.usage.output_tokens,
                "model": self.model,
                "metadata": {
                    "stop_reason": response.stop_reason,
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
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
