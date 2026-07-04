import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("../.env")   # because .env is in root

api_key = os.getenv("OPENAI_API_KEY")
print("Key loaded:", api_key[:15], "...")

client = OpenAI(api_key=api_key)

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "user", "content": "Say hello"}
    ]
)

print(response.choices[0].message.content)