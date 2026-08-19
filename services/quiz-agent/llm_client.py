import json
import os
import openai

MODEL = os.getenv("QUIZ_LLM_MODEL", "gpt-4o-mini")


def _client() -> openai.AsyncOpenAI:
    return openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def generate_quiz_questions(subject: str, source_text: str, num_questions: int, difficulty: str) -> list[dict]:
    """Ask the LLM for a strict-JSON set of multiple-choice questions."""
    prompt = f"""You are a quiz generator for the subject "{subject}".
Difficulty: {difficulty}.
Based on the following source material, write exactly {num_questions} multiple-choice questions.

Source material:
\"\"\"{source_text}\"\"\"

Respond with ONLY a JSON object of this exact shape, no prose:
{{
  "questions": [
    {{
      "question": "string",
      "choices": ["string", "string", "string", "string"],
      "correct_index": 0,
      "explanation": "string"
    }}
  ]
}}
"""
    response = await _client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You generate strictly valid JSON quiz content."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        response_format={"type": "json_object"},
    )
    parsed = json.loads(response.choices[0].message.content)
    return parsed["questions"]
