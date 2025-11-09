# 1
import json
from openai import OpenAI

client = OpenAI(
    api_key = ""
)

# 2
system_prompt = """
You are a dungeon master for a DND game. A user will give you a brief description of the world they are playing in. 

Given a description of the fantasy world, come up with a name and description for each party member, and respond with a JSON in the following format:

{
    "NAME_1": "DESCRIPTION_1",
    "NAME_2": "DESCRIPTION_2"
}
"""

# 3
user_prompt = input("Describe the world that you will be playing in.")

# 4
response = client.chat.completions.create(
    model="gpt-4o",
    response_format={ "type": "json_object" },
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
)

# 5
print(json.loads(response.choices[0].message.content))