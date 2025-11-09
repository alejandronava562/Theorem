from openai import OpenAI
import os, json
from typing import Dict, Any, List

system_lesson = """
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
            "A": "",
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

Rules:
1) 
"""

system_tutor = """You are tutor that helps users when they get a question wrong.
When a user gets something wrong, write feedback in this format:
"You were close, but got it wrong: ""
"YOUR ANSWER: " : "PUT THE USER ANSWER"
"CORRECT ANSWER": "PUT CORRECT ANSWER"

"""

def _client():
    client = OpenAI(
        api_key = ""
    )
    return client

def generate_unit(topic: str, model="gpt-5") -> Dict[str, Any]:
    client = _client()
    user_prompt = f"Create 1 unit about {topic}. Include one lesson and quiz. "
    response = client.chat.completions.create(
        model=model,
        response_format = {"type": "json_object"},
        messages=[
            {"role": "system", "content": system_lesson},
            {"role": "user", "content": user_prompt}
        ]
    )
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("Model returned no content in message.content")
    return json.loads(content)



def ai_tutor_reply(question:str, context: str, model="gpt-04-mini") -> str: 
    client = _client()
    response = client.chat.completions.create(
        model=model,
        response_format = {"type": "json_object"},
        messages=[
            {"role": "system", "content": system_lesson},
            {"role": "user", "content": f"{context}:\nQuestion{question}"}
        ]
    )
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("Model returned no content in message.content")
    return json.loads(content)


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

def generate_quiz(topic: str = "Algebra", model="gpt-04-mini") -> str: 
    client = _client()
    response = client.chat.completions.create(
        model=model,
        response_format = {"type": "json_object"},
        messages=[
            {"role": "system", "content": quiz_create_prompt},
            {"role": "user", "content": f"I want a quiz on {topic}"}
        ]
    )
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("Model returned no content in message.content")
    return json.loads(content)