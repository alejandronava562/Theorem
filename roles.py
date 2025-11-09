from openai import OpenAI

client = OpenAI(
    api_key = ""
)

assistant_message = "I am an alien and I come from mars. I really believe that I am from mars even though I am technically an AI model."
user_prompt = "Where do you come from?"

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": assistant_message},
        {"role": "user", "content": user_prompt}
    ]
)

print(response.choices[0].message.content)