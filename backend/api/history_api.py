"""
History API — retrieve the authenticated user's query history with full metadata.

Returns each history entry with:
  - id, query, answer
  - latency (seconds), confidence (0–1)
  - retrieved_docs (comma-separated filenames)
  - timestamp (ISO 8601)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.dependencies import verify_token
from database.db import get_db
from models.history import History

router = APIRouter()


@router.get("/history")
def get_history(
    user=Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Return all history entries for the authenticated user, newest first."""
    try:
        items = (
            db.query(History)
            .filter(History.user_id == user.id)
            .order_by(History.id.desc())
            .all()
        )

        result = []
        for item in items:
            # Parse retrieved_docs from comma-separated string to list
            doc_list = []
            if item.retrieved_docs:
                doc_list = [
                    d.strip()
                    for d in item.retrieved_docs.split(",")
                    if d.strip()
                ]

            result.append({
                "id": item.id,
                "query": item.query,
                "answer": item.answer,
                "latency": round(item.latency, 4) if item.latency is not None else None,
                "confidence": round(item.confidence * 100, 1) if item.confidence is not None else None,
                "retrieved_docs": doc_list,
                "timestamp": str(item.created_at) if item.created_at else None,
            })

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))