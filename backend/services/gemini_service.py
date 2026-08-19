from .base_service import BaseLLMService
from typing import Dict, Any
import google.generativeai as genai
import os

class GeminiService(BaseLLMService):
    """Service for Google Gemini models"""

    def __init__(self, api_key: str = None, model: str = "gemini-2.5-flash", temperature: float = 0.7, max_tokens: int = 1000):
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        super().__init__(api_key, model, temperature, max_tokens)
        genai.configure(api_key=self.api_key)
        self.model_instance = genai.GenerativeModel(self.model)

    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response using Google Gemini API"""
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens
            )

            response = await self.model_instance.generate_content_async(
                prompt,
                generation_config=generation_config
            )

            return {
                "response_text": response.text,
                "token_count": None,  # Gemini doesn't provide token counts in the same way
                "model": self.model,
                "metadata": {
                    "finish_reason": response.candidates[0].finish_reason.name if response.candidates else None,
                    "safety_ratings": [
                        {
                            "category": rating.category.name,
                            "probability": rating.probability.name
                        }
                        for rating in response.candidates[0].safety_ratings
                    ] if response.candidates else []
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
