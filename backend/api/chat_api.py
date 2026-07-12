"""
Chat API — Full CRUD for chat sessions + RAG-powered messaging.

Endpoints
---------
POST   /chat                       — Legacy single-question endpoint (backward compat)
GET    /chats                      — List all chats for the authenticated user
POST   /chats                      — Create a new chat session
GET    /chats/{chat_id}            — Get a chat with its messages
DELETE /chats/{chat_id}            — Delete a chat and all its messages
POST   /chats/{chat_id}/messages   — Send a message, get a RAG-powered response
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.dependencies import verify_token
from database.db import get_db
from models.chat import Chat, ChatMessage
from services.search_service import answer_from_documents

router = APIRouter()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Number of recent conversation turns to include as context for multi-turn memory
CONVERSATION_MEMORY_TURNS = 10


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_conversation_context(messages: list[ChatMessage]) -> str:
    """
    Build a concise conversation history string from the most recent messages.
    Used to provide multi-turn memory to the RAG pipeline.
    """
    recent = messages[-CONVERSATION_MEMORY_TURNS:]
    lines = []
    for msg in recent:
        role_label = "User" if msg.role == "user" else "Assistant"
        # Truncate long assistant replies to keep the context window manageable
        content = msg.content
        if msg.role == "assistant" and len(content) > 500:
            content = content[:500] + "…"
        lines.append(f"{role_label}: {content}")
    return "\n".join(lines)


def _chat_summary(chat: Chat) -> dict:
    """Serialise a Chat row into the shape the frontend expects."""
    return {
        "id": chat.id,
        "title": chat.title,
        "created_at": str(chat.created_at) if chat.created_at else None,
        "updated_at": str(chat.updated_at) if chat.updated_at else None,
        "message_count": len(chat.messages) if chat.messages else 0,
    }


# ---------------------------------------------------------------------------
# Legacy endpoint — kept for backward compatibility
# ---------------------------------------------------------------------------


@router.post("/chat")
def chat_legacy(
    data: dict,
    user=Depends(verify_token),
    db: Session = Depends(get_db),
):
    """
    Legacy single-shot chat endpoint.
    Accepts ``{ "question": "..." }`` and returns the RAG result.
    """
    question = (data.get("question") or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    result = answer_from_documents(user=user, db=db, query=question)
    db.commit()
    return result


# ---------------------------------------------------------------------------
# Chat CRUD
# ---------------------------------------------------------------------------


@router.get("/chats")
def list_chats(
    user=Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Return all chat sessions for the authenticated user, newest first."""
    chats = (
        db.query(Chat)
        .filter(Chat.user_id == user.id)
        .order_by(Chat.updated_at.desc())
        .all()
    )
    return [_chat_summary(c) for c in chats]


@router.post("/chats")
def create_chat(
    data: dict,
    user=Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Create a new chat session."""
    title = (data.get("title") or "New Chat").strip()

    chat = Chat(title=title, user_id=user.id)
    db.add(chat)
    db.commit()
    db.refresh(chat)

    return _chat_summary(chat)


@router.get("/chats/{chat_id}")
def get_chat(
    chat_id: int,
    user=Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Get a single chat with all its messages."""
    chat = (
        db.query(Chat)
        .filter(Chat.id == chat_id, Chat.user_id == user.id)
        .first()
    )

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "created_at": str(msg.created_at) if msg.created_at else None,
        }
        for msg in (chat.messages or [])
    ]

    return {
        **_chat_summary(chat),
        "messages": messages,
    }


@router.delete("/chats/{chat_id}")
def delete_chat(
    chat_id: int,
    user=Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Delete a chat and all its messages (cascade)."""
    chat = (
        db.query(Chat)
        .filter(Chat.id == chat_id, Chat.user_id == user.id)
        .first()
    )

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    db.delete(chat)
    db.commit()

    return {"message": "Chat deleted successfully"}


# ---------------------------------------------------------------------------
# Messaging with RAG
# ---------------------------------------------------------------------------


@router.post("/chats/{chat_id}/messages")
def send_message(
    chat_id: int,
    data: dict,
    user=Depends(verify_token),
    db: Session = Depends(get_db),
):
    """
    Send a user message and receive a RAG-powered assistant reply.

    Request body: ``{ "message": "..." }``

    Returns:
        - user_message      : the persisted user message
        - assistant_message  : the persisted assistant reply
        - sources            : source citations from the RAG pipeline
        - chat               : updated chat summary (title may change)
    """
    text = (data.get("message") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message is required")

    chat = (
        db.query(Chat)
        .filter(Chat.id == chat_id, Chat.user_id == user.id)
        .first()
    )
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # ── Persist user message ──────────────────────────────────────────────
    user_msg = ChatMessage(chat_id=chat.id, role="user", content=text)
    db.add(user_msg)
    db.flush()

    # ── Build conversation context for multi-turn memory ──────────────────
    existing_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.chat_id == chat.id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    # Exclude the just-added user message from context (it IS the current query)
    history_messages = [m for m in existing_messages if m.id != user_msg.id]
    conversation_context = _build_conversation_context(history_messages) if history_messages else None

    # ── Run RAG pipeline ──────────────────────────────────────────────────
    result = answer_from_documents(
        user=user,
        db=db,
        query=text,
        conversation_context=conversation_context,
    )

    answer_text = result.get("answer", "No relevant information found in uploaded documents.")
    sources = result.get("sources", [])

    # ── Persist assistant message ─────────────────────────────────────────
    assistant_msg = ChatMessage(
        chat_id=chat.id,
        role="assistant",
        content=answer_text,
    )
    db.add(assistant_msg)

    # ── Auto-title: use the first user message as the chat title ──────────
    if chat.title == "New Chat" and text:
        chat.title = text[:80] + ("…" if len(text) > 80 else "")

    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)
    db.refresh(chat)

    return {
        "user_message": {
            "id": user_msg.id,
            "role": user_msg.role,
            "content": user_msg.content,
            "created_at": str(user_msg.created_at) if user_msg.created_at else None,
        },
        "assistant_message": {
            "id": assistant_msg.id,
            "role": assistant_msg.role,
            "content": assistant_msg.content,
            "created_at": str(assistant_msg.created_at) if assistant_msg.created_at else None,
        },
        "sources": sources,
        "chat": _chat_summary(chat),
    }