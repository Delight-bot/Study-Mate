import json
import os
import openai

MODEL = os.getenv("FLASHCARD_LLM_MODEL", "gpt-4o-mini")


def _client() -> openai.AsyncOpenAI:
    return openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def generate_flashcards(subject: str, source_text: str, count: int) -> list[dict]:
    """Ask the LLM for a strict-JSON set of front/back flashcard pairs."""
    prompt = f"""You are a flashcard generator for the subject "{subject}".
Based on the following source material, write exactly {count} flashcards, each a concise
question/prompt on the front and a concise answer on the back.

Source material:
\"\"\"{source_text}\"\"\"

Respond with ONLY a JSON object of this exact shape, no prose:
{{
  "flashcards": [
    {{ "front": "string", "back": "string" }}
  ]
}}
"""
    response = await _client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You generate strictly valid JSON flashcard content."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        response_format={"type": "json_object"},
    )
    parsed = json.loads(response.choices[0].message.content)
    return parsed["flashcards"]
