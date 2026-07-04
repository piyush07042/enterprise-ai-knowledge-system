import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def ask_groq(context, question):
    try:
        prompt = f"""
You are an AI assistant answering questions from documents.

Instructions:
- Use ONLY the context below.
- OCR/PDF text may contain broken symbols, weird spacing, or formatting issues.
- Ignore formatting issues and extract the meaning.
- If the answer exists in context, answer clearly.
- If answer does not exist, reply exactly:
No relevant information found.

Context:
{context}

Question:
{question}

Answer:
"""

        print("Question:", question)
        print("Context length:", len(context))

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        return response.choices[0].message.content

    except Exception as e:
        print("GROQ ERROR:", str(e))
        raise Exception(f"Groq failed: {str(e)}")