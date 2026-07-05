from fastapi import APIRouter, Depends, HTTPException
from auth.dependencies import verify_token
from database.db import get_db
from sqlalchemy.orm import Session
from models.document import Document
from models.history import History
from services.vector_service import collection
import re

router = APIRouter()

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

        # -------------------------
        # REAL VECTOR COUNT
        # -------------------------
        vector_data = collection.get(
            where={"user_id": int(user.id)},
            include=[]
        )

        vectors = len(vector_data.get("ids", []))

        queries = query_counts.get(user.email, 0)

        history_count = db.query(History).filter(
            History.user_id == user.id
        ).count()

        history_records = db.query(History).filter(
            History.user_id == user.id
        ).all()

        # Average latency
        latencies = [
            h.latency
            for h in history_records
            if h.latency is not None
        ]

        avg_latency = (
            sum(latencies) / len(latencies)
            if latencies else 0.0
        )

        # Average confidence
        confidences = [
            h.confidence
            for h in history_records
            if h.confidence is not None
        ]

        avg_confidence = (
            sum(confidences) / len(confidences)
            if confidences else 0.0
        )

        # Most searched document
        doc_counts = {}

        for h in history_records:
            if h.retrieved_docs:
                for doc in h.retrieved_docs.split(","):
                    doc = doc.strip()

                    if doc:
                        doc_counts[doc] = doc_counts.get(doc, 0) + 1

        most_searched_doc = (
            max(doc_counts, key=doc_counts.get)
            if doc_counts else "N/A"
        )

        stop_words = {
            "a","an","and","are","as","at","be","by","for","from",
            "in","is","it","me","of","on","or","pdf","tell",
            "the","to","what","which","who","with","show",
            "summarize","summary","all","my","uploaded",
            "documents","files","document","file"
        }

        keyword_counts = {}

        for h in history_records:

            if h.query:

                words = re.findall(
                    r"[a-z0-9]+",
                    h.query.lower()
                )

                for word in words:

                    if len(word) > 1 and word not in stop_words:

                        keyword_counts[word] = (
                            keyword_counts.get(word, 0) + 1
                        )

        top_keyword = (
            max(keyword_counts, key=keyword_counts.get)
            if keyword_counts else "N/A"
        )

        return {
            "documents": documents,
            "vectors": vectors,
            "queries": queries,
            "history": history_count,
            "avg_latency": round(avg_latency, 2),
            "avg_confidence": round(avg_confidence * 100, 1)
            if confidences else 0.0,
            "most_searched_doc": most_searched_doc,
            "top_keyword": top_keyword
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )