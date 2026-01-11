from openai import OpenAI
import json
from typing import Dict, Any

from env_loader import get_openai_api_key

SYSTEM_UNIT = """
You are a Duolingo-style micro-lesson + quiz generator.
Output ONLY valid JSON matching this exact schema:

{
  "UNITNUMBER": "<string>",
  "TITLE": "<string>",
  "LESSON1": "<string>",
  "LESSON1CONTENT": [
    { "TYPE": "LESSON", "TEXT": "<string>" },
    {
      "TYPE": "QUIZ",
      "QUESTIONS": [
        {
          "QUESTION_NUMBER": "<string>",
          "QUESTION": "<string>",
          "OPTIONS": { "A": "<string>", "B": "<string>", "C": "<string>", "D": "<string>" },
          "CORRECT_ANSWER": "A|B|C|D"
        }
      ]
    }
  ]
}

Rules:
- EXACTLY 2 items in LESSON1CONTENT: one LESSON then one QUIZ.
- EXACTLY 5 QUESTIONS.
- Keep lesson short (120-220 words), age-appropriate, and focused.
- Quiz difficulty matches the lesson.
- No extra keys anywhere.
"""

quiz_create_prompt = """
You are a curriculum generator for the subject of Algebra. Output a strict JSON object that matches this format:
{
  "UNITNUMBER": "1",
  "TITLE": "Algebra",
  "LESSON1": "Variables",
  "LESSON1CONTENT": [
    {
      "TYPE": "LESSON",
      "TEXT": "Write the lesson here."
    },
    {
      "TYPE": "QUIZ",
      "QUESTIONS": [
        {
          "QUESTION_NUMBER": "1",
          "QUESTION": "In 3x + 2 = 11, what is the variable",
          "OPTIONS": {
            "A": "3",
            "B": "x",
            "C": "2",
            "D": "11"
          },
          "CORRECT_ANSWER": "B"
        },
        {
          "QUESTION_NUMBER": "2",
          "QUESTION": "Which symbol represents an inequality",
          "OPTIONS": {
            "A": "=",
            "B": "<",
            "C": "+",
            "D": "x"
          },
          "CORRECT_ANSWER": "B"
        }
      ]
    }
  ]
}
"""


def _client():
    return OpenAI(api_key=get_openai_api_key())


def generate_unit(
    topic: str,
    model: str = "gpt-4o-mini",
    *,
    unit_title: str | None = None,
    skills: list[str] | None = None,
) -> Dict[str, Any]:
    client = _client()
    focus = ""
    if unit_title:
        focus += f'Unit title: "{unit_title}". '
    if skills:
        focus += "Focus skills: " + ", ".join(skills) + ". "
    user_prompt = f"Create 1 unit about {topic}. {focus}Include one lesson and a 5-question multiple-choice quiz."
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_UNIT},
            {"role": "user", "content": user_prompt}
        ]
    )
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("Model returned no content in message.content")
    return json.loads(content)


def generate_quiz(topic: str = "Algebra", model: str = "gpt-4o-mini") -> Dict[str, Any]:
    client = _client()
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": quiz_create_prompt},
            {"role": "user", "content": f"I want a quiz on {topic}"}
        ]
    )
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("Model returned no content in message.content")
    return json.loads(content)
