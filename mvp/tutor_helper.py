from openai import OpenAI
import json
from typing import Any, Dict

system_tutor = """You are tutor that helps users when they get a question wrong.
When a user gets something wrong, write feedback in this format:
"You were close, but got it wrong: ""
"YOUR ANSWER: " : "PUT THE USER ANSWER"
"CORRECT ANSWER": "PUT CORRECT ANSWER"

"""


def _client():
    client = OpenAI(
        api_key=""
    )
    return client


def ai_tutor_reply(question: str, context: str, model="gpt-04-mini") -> Dict[str, Any]:
    client = _client()
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_tutor},
            {"role": "user", "content": f"{context}:\nQuestion{question}"}
        ]
    )
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("Model returned no content in message.content")
    return json.loads(content)
