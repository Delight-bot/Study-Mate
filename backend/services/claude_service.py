from .base_service import BaseLLMService
from typing import Dict, Any
import anthropic
import os

class ClaudeService(BaseLLMService):
    """Service for Anthropic Claude models"""

    # claude-3-5-sonnet-20241022 was retired; claude-haiku-4-5 is the
    # current fast/cheap tier, matching gpt-4o-mini and gemini-3.6-flash
    # as the comparison feature's speed/cost-conscious default.
    def __init__(self, api_key: str = None, model: str = "claude-haiku-4-5-20251001", temperature: float = 0.7, max_tokens: int = 1000):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        super().__init__(api_key, model, temperature, max_tokens)
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)

    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using Anthropic Claude API"""
        try:
            # anthropic>=2.0 dropped `temperature` from messages.create()
            # entirely (replaced by speed/thinking/service_tier) — self.temperature
            # is kept on the instance for BaseLLMService's uniform constructor,
            # just not forwarded to this call anymore.
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
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
