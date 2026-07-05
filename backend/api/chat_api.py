from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.dependencies import verify_token
from database.db import get_db
from models.chat import Chat, ChatMessage
from services.search_service import answer_from_documents

router = APIRouter()


class ChatCreateRequest(BaseModel):
    title: str | None = None


class ChatMessageRequest(BaseModel):
    message: str


def serialize_message(message):
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat() if message.created_at else None
    }


def serialize_chat(chat, include_messages=False):
    data = {
        "id": chat.id,
        "title": chat.title,
        "created_at": chat.created_at.isoformat() if chat.created_at else None,
        "updated_at": chat.updated_at.isoformat() if chat.updated_at else None,
        "message_count": len(chat.messages)
    }

    if include_messages:
        data["messages"] = [serialize_message(message) for message in chat.messages]

    return data


def get_user_chat(chat_id, user, db):
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == user.id
    ).first()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    return chat


@router.get("/chats")
def list_chats(
    user=Depends(verify_token),
    db: Session = Depends(get_db)
):
    chats = db.query(Chat).filter(
        Chat.user_id == user.id
    ).order_by(Chat.updated_at.desc()).all()

    return [serialize_chat(chat) for chat in chats]


@router.post("/chats")
def create_chat(
    request: ChatCreateRequest,
    user=Depends(verify_token),
    db: Session = Depends(get_db)
):
    chat = Chat(
        title=(request.title or "New Chat").strip() or "New Chat",
        user_id=user.id
    )

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return serialize_chat(chat, include_messages=True)


@router.get("/chats/{chat_id}")
def get_chat(
    chat_id: int,
    user=Depends(verify_token),
    db: Session = Depends(get_db)
):
    chat = get_user_chat(chat_id, user, db)
    return serialize_chat(chat, include_messages=True)


@router.post("/chats/{chat_id}/messages")
def send_message(
    chat_id: int,
    request: ChatMessageRequest,
    user=Depends(verify_token),
    db: Session = Depends(get_db)
):
    text = request.message.strip()

    if not text:
        raise HTTPException(status_code=400, detail="Message is required")

    chat = get_user_chat(chat_id, user, db)

    previous_messages = db.query(ChatMessage).filter(
        ChatMessage.chat_id == chat.id
    ).order_by(ChatMessage.created_at.asc()).all()

    recent_messages = previous_messages[-10:]
    conversation_context = "\n".join([
        f"{message.role}: {message.content}"
        for message in recent_messages
    ])

    user_message = ChatMessage(
        chat_id=chat.id,
        role="user",
        content=text
    )
    db.add(user_message)

    if chat.title == "New Chat":
        chat.title = text[:60]

    # answer_from_documents returns {"answer": "...", "sources": [...]}
    # Sources are ephemeral — returned in the response but NOT persisted to the DB.
    result = answer_from_documents(
        user=user,
        db=db,
        query=text,
        conversation_context=conversation_context
    )

    answer = result["answer"]
    sources = result.get("sources", [])

    assistant_message = ChatMessage(
        chat_id=chat.id,
        role="assistant",
        content=answer
    )
    db.add(assistant_message)

    chat.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    db.refresh(chat)

    return {
        "chat": serialize_chat(chat),
        "user_message": serialize_message(user_message),
        "assistant_message": serialize_message(assistant_message),
        # Citations are ephemeral — not stored in DB, returned only at send time.
        "sources": sources,
    }


@router.delete("/chats/{chat_id}")
def delete_chat(
    chat_id: int,
    user=Depends(verify_token),
    db: Session = Depends(get_db)
):
    chat = get_user_chat(chat_id, user, db)
    db.delete(chat)
    db.commit()

    return {"message": "Chat deleted"}
