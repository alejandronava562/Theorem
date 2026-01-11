from openai import OpenAI
import json
from typing import Any, Dict

from env_loader import get_openai_api_key

SYSTEM_TUTOR = """
You are a friendly tutor that helps users when they get a quiz question wrong.
Output ONLY valid JSON matching this exact schema:

{
  "message": "<short encouraging message>",
  "explanation": "<2-4 sentence explanation>",
  "user_answer": "<what the user chose (letter + meaning)>",
  "correct_answer": "<the correct choice (letter + meaning)>"
}

Rules:
- No extra keys anywhere.
- Keep it concise.
"""


def _client():
    return OpenAI(api_key=get_openai_api_key())


def ai_tutor_reply(question: str, context: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    client = _client()
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_TUTOR},
            {"role": "user", "content": f"{context}:\nQuestion{question}"}
        ]
    )
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("Model returned no content in message.content")
    return json.loads(content)
