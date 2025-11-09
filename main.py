# 1
from openai import OpenAI

# 2
client = OpenAI(
    api_key = ""
)
# 3
user_prompt = "Explain in 3 sentences who William Shakespeare was."

# 4
response = client.chat.completions.create(
    model="gpt-5",
    messages=[
        {"role": "user", "content": user_prompt}
    ]
)

# 5
print(response)
print(response.choices[0].message.content)