from openai import OpenAI
import json
from typing import Any, Dict

from env_loader import get_openai_api_key
# Generates structured learning path using OpenAI (Duolingo-style levels and units)
# Prompt template defining JSON format for learning path generation
SYSTEM_PATH = """
Generate a Duolingo-style learning path outline. Output ONLY a strict JSON object matching exactly:

{
  "learning_path": {
    "subject": "<string>",
    "description": "<string>",
    "levels": [
      {
        "level": <number>,
        "title": "<string>",
        "goal": "<string>",
        "units": [
          {
            "unit": <number>,
            "title": "<string>",
            "skills": ["<string>"]
          }
        ]
      }
    ]
  }
}

Rules:
- 5 levels exactly (1-5)
- 2 units per level exactly (10 units total)
- 3 skills per unit exactly
- Skills are short phrases (2-6 words)
- No extra keys anywhere
- Valid JSON only
"""
# Creates OpenAI client using API key 
def _client():
    return OpenAI(api_key=get_openai_api_key())
# Calls OpenAI to generate learning path JSON for a given topic
def generate_pathway(topic: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    client = _client()
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role" : "system", "content": SYSTEM_PATH},
            {"role": "user", "content": f"Create a learning path for {topic}"}
        ]
    )
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("Model returned no path content!")
    return json.loads(content)
