from abc import ABC, abstractmethod
from typing import Dict, Any
import time

class BaseLLMService(ABC):
    """Abstract base class for LLM services"""

    def __init__(self, api_key: str, model: str, temperature: float = 0.7, max_tokens: int = 1000):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a response from the LLM

        Returns:
            Dict containing:
                - response_text: str
                - response_time: float (in seconds)
                - token_count: int (optional)
                - metadata: dict (optional)
        """
        pass

    async def timed_generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Wrapper to time the response generation"""
        start_time = time.time()
        result = await self.generate_response(prompt, **kwargs)
        end_time = time.time()

        result['response_time'] = end_time - start_time
        return result

    def format_prompt(self, question: str, context: str = None, style: str = None) -> str:
        """Format the prompt based on user preferences"""
        base_prompt = question

        if context:
            base_prompt = f"Context: {context}\n\nQuestion: {question}"

        if style == 'detailed':
            base_prompt += "\n\nPlease provide a detailed explanation with examples."
        elif style == 'concise':
            base_prompt += "\n\nPlease provide a concise, direct answer."
        elif style == 'examples-heavy':
            base_prompt += "\n\nPlease include multiple examples in your explanation."

        return base_prompt
