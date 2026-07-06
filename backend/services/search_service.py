from api.stats_api import query_counts
from models.document import Document
from services.document_sync_service import sync_user_upload_documents
from models.history import History
from services.llm_service import generate_answer
from services.vector_service import search_documents
import time
import os
import datetime


ALL_DOCUMENT_QUERY_PHRASES = [
    "summarize my uploaded documents",
    "summarize all documents",
    "summarize all uploaded documents",
    "summary of my uploaded documents",
    "summary of all documents",
    "what documents have i uploaded",
    "which documents have i uploaded",
    "list my uploaded documents",
    "show my uploaded documents",
    "summarize documents",
    "summarize everything",
    "summarize all files",
    "summarize my files",
    "list all files",
    "what files do i have",
    "what have i uploaded"
]


def is_all_documents_query(query):
    normalized_query = " ".join((query or "").lower().split())

    if normalized_query in ALL_DOCUMENT_QUERY_PHRASES:
        return True

    return (
        ("summarize" in normalized_query or "summary" in normalized_query)
        and "document" in normalized_query
        and (
            "uploaded" in normalized_query
            or "all" in normalized_query
            or "my" in normalized_query
        )
    )


def _strip_text_field(sources):
    """
    Remove the internal 'text' field from source objects before returning to the API.
    The 'text' field is only used internally to build LLM context strings.
    """
    return [
        {
            "filename": s["filename"],
            "chunk_index": s["chunk_index"],
            "score": s["score"],
            "preview": s["preview"],
        }
        for s in sources
    ]


def _build_rag_context(sources):
    """
    Build the context string for the LLM from structured source objects.
    Uses the full 'text' field (not the truncated 'preview').
    """
    parts = []
    for s in sources:
        parts.append(
            f"Source: {s['filename']}\n"
            f"Chunk: {s['chunk_index']}\n"
            f"Content:\n{s['text']}"
        )
    return "\n\n".join(parts)


def get_all_user_document_context(user, db):
    sync_user_upload_documents(user, db)
    db.flush()

    documents = (
        db.query(Document)
        .filter(Document.user_id == user.id)
        .order_by(Document.id.asc())
        .all()
    )

    filenames = []
    context_parts = []

    for document in documents:
        filenames.append(document.filename)

        content = " ".join((document.content or "").split())

        if not content:
            content = "No extractable text found."

        context_parts.append(
            f"Source: {document.filename}\n\n{content}"
        )

    return filenames, "\n\n".join(context_parts)


def log_rag(query, retrieved_docs, latency, confidence):
    """
    Log retrieval metadata to backend/logs/rag.log
    """
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "rag.log")
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    docs_str = ", ".join(retrieved_docs) if retrieved_docs else "None"
    conf_str = f"{confidence * 100:.1f}%" if confidence is not None else "N/A"
    
    log_line = f"[{timestamp}] Query: \"{query}\" | Latency: {latency:.4f}s | Confidence: {conf_str} | Retrieved: [{docs_str}]\n"
    
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        print("Failed to write to rag.log:", e)


def answer_from_documents(user, db, query, conversation_context=None):
    """
    Run the RAG pipeline and return a structured result:

        {
            "answer": "...",
            "sources": [
                {
                    "filename": "resume.pdf",
                    "chunk_index": 3,
                    "score": 0.91,       # None for all-documents path
                    "preview": "..."
                },
                ...
            ],
            "metrics": {
                "retrieval_time": 0.1234,
                "generation_time": 1.2345,
                "total_time": 1.3579
            }
        }

    The 'sources' list is safe for direct API serialisation — the internal
    'text' field used for LLM context is stripped before returning.
    """
    start_total = time.time()

    # ----------- SUMMARIZE ALL DOCUMENTS -----------
    if is_all_documents_query(query):
        start_retrieval = time.time()
        filenames, context = get_all_user_document_context(user, db)
        retrieval_time = time.time() - start_retrieval

        start_generation = time.time()
        if not filenames:
            answer = "No uploaded documents found."
            api_sources = []
            generation_time = 0.0
        else:
            question = f"""
The user asked:

{query}

Uploaded files:

{chr(10).join("- " + f for f in filenames)}

Instructions:

1. Use ALL uploaded documents.
2. Never ignore any uploaded file.
3. Mention EVERY filename.
4. Summarize EVERY document separately.
5. Finish with one overall summary.
"""
            answer = generate_answer(context, question)
            generation_time = time.time() - start_generation

            # For the all-documents path there is no vector similarity —
            # score is None and confidence will display as "All Documents".
            api_sources = [
                {
                    "filename": filename,
                    "chunk_index": 0,
                    "score": None,
                    "preview": "",
                }
                for filename in filenames
            ]

        total_time = time.time() - start_total

        # Log search details
        log_rag(query, filenames, total_time, None)

        query_counts[user.email] = query_counts.get(user.email, 0) + 1

        history = History(
            query=query,
            answer=answer,
            user_id=user.id,
            latency=total_time,
            confidence=None,
            retrieved_docs=",".join(filenames)
        )
        db.add(history)

        return {
            "answer": answer,
            "sources": api_sources,
            "metrics": {
                "retrieval_time": round(retrieval_time, 4),
                "generation_time": round(generation_time, 4),
                "total_time": round(total_time, 4)
            }
        }

    # ----------- NORMAL RAG SEARCH -----------

    retrieval_query = query

    if conversation_context:
        retrieval_query = (
            f"{query}\n\nRecent conversation:\n{conversation_context}"
        )

    start_retrieval = time.time()
    # search_documents now returns structured source objects (top 5, unique, with BM25 + Chroma + RRF)
    sources = search_documents(user.id, retrieval_query)
    retrieval_time = time.time() - start_retrieval

    start_generation = time.time()
    if not sources:
        answer = "No relevant document found."
        api_sources = []
        generation_time = 0.0
        avg_confidence = 0.0
        retrieved_filenames = []
    else:
        # Build LLM context from full text (uses internal 'text' field)
        context = _build_rag_context(sources[:5])

        question = query

        if conversation_context:
            question = f"""
Previous conversation:

{conversation_context}

Current Question:

{query}
"""

        answer = generate_answer(context, question)
        generation_time = time.time() - start_generation

        # Calculate average confidence
        valid_scores = [s["score"] for s in sources[:5] if s["score"] is not None]
        avg_confidence = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0

        # Strip internal 'text' field — safe for API serialisation
        api_sources = _strip_text_field(sources[:5])
        retrieved_filenames = list({s["filename"] for s in sources[:5]})

    total_time = time.time() - start_total

    # Log search details
    log_rag(query, retrieved_filenames, total_time, avg_confidence if sources else None)

    query_counts[user.email] = query_counts.get(user.email, 0) + 1

    history = History(
        query=query,
        answer=answer,
        user_id=user.id,
        latency=total_time,
        confidence=avg_confidence if sources else None,
        retrieved_docs=",".join(retrieved_filenames)
    )
    db.add(history)

    return {
        "answer": answer,
        "sources": api_sources,
        "metrics": {
            "retrieval_time": round(retrieval_time, 4),
            "generation_time": round(generation_time, 4),
            "total_time": round(total_time, 4)
        }
    }