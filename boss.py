from openai import OpenAI

client = OpenAI(
    api_key = ""
)
system_prompt = """
You work at a paint store. Customers come in looking to purchase paint products. Make sure you help them find what they need and mention the store's rewards system.
"""
user_prompt = input("Hi! Welcome to our paint store. How can we help you?")

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
)

print(response.choices[0].message.content)