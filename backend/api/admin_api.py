from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.db import get_db
from auth.admin_dependency import verify_admin

from models.user import User
from models.document import Document
from models.history import History

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats")
def admin_stats(
    admin=Depends(verify_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).count()

    documents = db.query(Document).count()

    history = db.query(History).count()

    return {
        "users": users,
        "documents": documents,
        "history": history
    }


@router.get("/users")
def get_users(
    admin=Depends(verify_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()

    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role
        }
        for u in users
    ]


@router.get("/documents")
def get_documents(
    admin=Depends(verify_admin),
    db: Session = Depends(get_db)
):
    docs = db.query(Document).all()

    return [
        {
            "id": d.id,
            "filename": d.filename,
            "user_id": d.user_id
        }
        for d in docs
    ]


@router.get("/history")
def get_history(
    admin=Depends(verify_admin),
    db: Session = Depends(get_db)
):
    history = db.query(History).all()

    return [
        {
            "id": h.id,
            "query": h.query,
            "user_id": h.user_id,
            "latency": h.latency,
            "confidence": h.confidence
        }
        for h in history
    ]