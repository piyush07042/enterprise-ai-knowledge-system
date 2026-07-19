"""
LLM Service — Production-quality Groq gateway for the RAG pipeline.

Responsibilities:
  - Enforce strict grounding: answer ONLY from provided document context
  - Always cite source filenames in the response
  - Never hallucinate — reply with a standard fallback when context is insufficient
  - Support multi-turn conversation via optional conversation_history
  - Use professional formatting (bullets, headings, bold)
"""

import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Groq client initialisation
# ---------------------------------------------------------------------------

client = None

_api_key = os.getenv("GROQ_API_KEY")
if _api_key:
    client = Groq(api_key=_api_key)

# ---------------------------------------------------------------------------
# System prompt — loaded once, reused for every request
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are the **Enterprise AI Knowledge Assistant**, a professional retrieval-augmented \
generation (RAG) system deployed inside an enterprise knowledge management platform.

━━━ STRICT RULES ━━━
1. Answer **ONLY** from the document context provided below. \
   Do NOT use any prior knowledge, training data, or assumptions.
2. **Always cite** the source filename(s) for every piece of information you reference \
   (e.g., "According to *leave_policy.pdf*…").
3. If the document context **contains information related** to the user's question, \
   extract and present that information — even if it only partially addresses the question.
4. Only if the provided context is **completely unrelated** to the question and contains \
   **no useful information** at all, respond with: \
   "No relevant information found in uploaded documents."
5. **Never hallucinate**, fabricate, or guess information that is not explicitly stated \
   in the context.
6. If the context contains OCR artifacts, broken formatting, or unusual spacing, \
   interpret the content to the best of your ability and extract the intended meaning.

━━━ FORMATTING GUIDELINES ━━━
• Use **bold** for key terms and headings.
• Use bullet points or numbered lists for multi-part answers.
• Keep answers concise, accurate, and professionally formatted.
• When summarising multiple documents, address each document separately before \
  providing an overall summary.
"""

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_answer(context: str, question: str, conversation_history: str = "") -> str:
    """
    Generate an answer using Groq LLM grounded in the provided context.

    Parameters
    ----------
    context : str
        The concatenated document chunks (with source metadata) to ground on.
    question : str
        The user's current question (may include conversation framing).
    conversation_history : str, optional
        Stringified prior conversation turns for multi-turn memory.

    Returns
    -------
    str
        The LLM-generated answer, or a fallback string.
    """

    # ── Guard: empty context ──────────────────────────────────────────────
    if not (context or "").strip():
        return "No relevant information found in uploaded documents."

    # ── Guard: Groq unavailable ───────────────────────────────────────────
    if client is None:
        return context  # Graceful degradation — return raw context

    # ── Build the user message ────────────────────────────────────────────
    user_parts = []

    if conversation_history:
        user_parts.append(
            "━━━ PREVIOUS CONVERSATION ━━━\n"
            f"{conversation_history}\n"
        )

    user_parts.append(
        "━━━ DOCUMENT CONTEXT ━━━\n"
        f"{context}\n"
    )

    user_parts.append(
        "━━━ USER QUESTION ━━━\n"
        f"{question}\n"
    )

    user_message = "\n".join(user_parts)

    # ── Call Groq ─────────────────────────────────────────────────────────
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.15,
            max_tokens=1500,
        )

        answer = response.choices[0].message.content
        return answer if answer else "No relevant information found in uploaded documents."

    except Exception as exc:
        print("LLM Error:", exc)
        # Graceful degradation — never crash the pipeline
        return context


class LLMServiceClass:
    @staticmethod
    def generate_answer(context: str = None, question: str = None, contexts: list = None, conversation_history: str = "", **kwargs) -> str:
        if contexts is not None:
            if isinstance(contexts, list):
                context = "\n\n".join(contexts)
            elif isinstance(contexts, str):
                context = contexts
        return generate_answer(context or "", question or "", conversation_history)


llm_service = LLMServiceClass()