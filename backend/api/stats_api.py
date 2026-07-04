
from fastapi import APIRouter, Depends, HTTPException
from auth.dependencies import verify_token
from database.db import get_db
from sqlalchemy.orm import Session
from models.document import Document
from models.history import History
import os

router = APIRouter()

BASE_UPLOAD_FOLDER = "uploads"

query_counts = {}


@router.get("/dashboard-stats")
def dashboard_stats(
    user=Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        documents = db.query(Document).filter(
            Document.user_id == user.id
        ).count()

        # Approx vector chunks estimate
        vectors = documents * 15

        queries = query_counts.get(user.email, 0)

        history_count = db.query(History).filter(
            History.user_id == user.id
        ).count()

        return {
            "documents": documents,
            "vectors": vectors,
            "queries": queries,
            "history": history_count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
