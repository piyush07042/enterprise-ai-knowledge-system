"""
Stats API — dashboard analytics for the authenticated user.

Returns:
  - documents      : total uploaded documents
  - vectors        : total vector chunks in ChromaDB
  - queries        : session query count (in-memory)
  - history        : total history entries in DB
  - avg_latency    : average pipeline latency (seconds)
  - avg_confidence : average confidence (percentage)
  - most_searched_doc : most frequently retrieved document
  - top_keyword    : most frequent search keyword
  - most_active_day: day of the week with the most queries
  - total_queries  : total queries from database history
"""

from collections import Counter
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import re

from auth.dependencies import verify_token
from database.db import get_db
from models.document import Document
from models.history import History
from services.vector_service import collection
from services.document_sync_service import sync_user_upload_documents

router = APIRouter()

# In-memory session query counter (reset on server restart)
query_counts = {}

# Stop words excluded from keyword analysis
_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "in", "is", "it", "me", "of", "on", "or", "pdf", "tell",
    "the", "to", "what", "which", "who", "with", "show",
    "summarize", "summary", "all", "my", "uploaded",
    "documents", "files", "document", "file",
}


@router.get("/dashboard-stats")
def dashboard_stats(
    user=Depends(verify_token),
    db: Session = Depends(get_db),
):
    try:
        # Sync database with files on disk
        sync_user_upload_documents(user, db)
        db.commit()

        # ── Document count ────────────────────────────────────────────────
        document_count = (
            db.query(Document)
            .filter(Document.user_id == user.id)
            .count()
        )

        # ── Vector count ──────────────────────────────────────────────────
        vector_data = collection.get(
            where={"user_id": int(user.id)},
            include=[],
        )
        vector_count = len(vector_data.get("ids", []))

        # ── Session query count ───────────────────────────────────────────
        session_queries = query_counts.get(user.email, 0)

        # ── History records ───────────────────────────────────────────────
        history_records = (
            db.query(History)
            .filter(History.user_id == user.id)
            .all()
        )
        history_count = len(history_records)

        # ── Average latency ──────────────────────────────────────────────
        latencies = [
            h.latency for h in history_records
            if h.latency is not None
        ]
        avg_latency = (
            sum(latencies) / len(latencies)
            if latencies else 0.0
        )

        # ── Average confidence ───────────────────────────────────────────
        confidences = [
            h.confidence for h in history_records
            if h.confidence is not None
        ]
        avg_confidence = (
            sum(confidences) / len(confidences)
            if confidences else 0.0
        )

        # ── Most retrieved document ──────────────────────────────────────
        doc_counter = Counter()
        for h in history_records:
            if h.retrieved_docs:
                for doc in h.retrieved_docs.split(","):
                    doc = doc.strip()
                    if doc:
                        doc_counter[doc] += 1

        most_searched_doc = (
            doc_counter.most_common(1)[0][0]
            if doc_counter else "N/A"
        )

        # ── Top keyword ──────────────────────────────────────────────────
        keyword_counter = Counter()
        for h in history_records:
            if h.query:
                words = re.findall(r"[a-z0-9]+", h.query.lower())
                for word in words:
                    if len(word) > 1 and word not in _STOP_WORDS:
                        keyword_counter[word] += 1

        top_keyword = (
            keyword_counter.most_common(1)[0][0]
            if keyword_counter else "N/A"
        )

        # ── Most active day ──────────────────────────────────────────────
        day_counter = Counter()
        for h in history_records:
            if h.created_at:
                # created_at may be a string (SQLite) or datetime
                if isinstance(h.created_at, str):
                    try:
                        dt = datetime.fromisoformat(h.created_at)
                        day_counter[dt.strftime("%A")] += 1
                    except (ValueError, TypeError):
                        pass
                elif isinstance(h.created_at, datetime):
                    day_counter[h.created_at.strftime("%A")] += 1

        most_active_day = (
            day_counter.most_common(1)[0][0]
            if day_counter else "N/A"
        )

        # ── Build response ───────────────────────────────────────────────
        return {
            "documents": document_count,
            "vectors": vector_count,
            "queries": session_queries,
            "history": history_count,
            "avg_latency": round(avg_latency, 2),
            "avg_confidence": (
                round(avg_confidence * 100, 1)
                if confidences else 0.0
            ),
            "most_searched_doc": most_searched_doc,
            "top_keyword": top_keyword,
            "most_active_day": most_active_day,
            "total_queries": history_count,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))