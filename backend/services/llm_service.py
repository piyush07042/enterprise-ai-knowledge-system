
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
print("GROQ KEY FOUND:", bool(API_KEY))

client = None

if API_KEY:
    client = Groq(api_key=API_KEY)


def generate_answer(context, question):
    if client is None:
        raise Exception("GROQ_API_KEY missing in backend/.env")

    prompt = f"""
You are an AI assistant for an enterprise knowledge system.

Use ONLY the document context to answer. The context may contain chunks from
multiple documents. Each chunk includes its source filename.

Context:
{context}

Question:
{question}

Rules:
- Answer in simple English
- Use all relevant chunks, not just the first one
- Mention important details from different documents when they help answer the question
- Keep the answer concise
- If answer not found, say: Not found in document
"""

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="llama-3.3-70b-versatile"
    )

    return chat_completion.choices[0].message.content
