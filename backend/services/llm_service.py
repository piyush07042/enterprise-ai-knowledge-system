import os
from groq import Groq

client = None

api_key = os.getenv("GROQ_API_KEY")

if api_key:
    client = Groq(api_key=api_key)


def generate_answer(context: str, question: str):
    """
    Generate answer using Groq.
    Falls back to returning retrieved context if Groq is unavailable.
    """

    if not context.strip():
        return "No relevant information found."

    if client is None:
        return context

    try:
        prompt = f"""
You are an Enterprise AI Knowledge Assistant.

Answer ONLY from the provided context.

Context:
{context}

Question:
{question}
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=1024
        )

        return response.choices[0].message.content

    except Exception as e:
        print("LLM Error:", e)
        return context