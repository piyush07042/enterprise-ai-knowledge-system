from api.stats_api import query_counts
from models.document import Document
from services.document_sync_service import sync_user_upload_documents
from models.history import History
from services.llm_service import generate_answer
from services.vector_service import search_documents


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
            ]
        }

    The 'sources' list is safe for direct API serialisation — the internal
    'text' field used for LLM context is stripped before returning.
    """

    # ----------- SUMMARIZE ALL DOCUMENTS -----------
    if is_all_documents_query(query):

        filenames, context = get_all_user_document_context(user, db)

        if not filenames:
            answer = "No uploaded documents found."
            api_sources = []

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

        query_counts[user.email] = query_counts.get(user.email, 0) + 1

        history = History(
            query=query,
            answer=answer,
            user_id=user.id
        )
        db.add(history)

        return {"answer": answer, "sources": api_sources}

    # ----------- NORMAL RAG SEARCH -----------

    retrieval_query = query

    if conversation_context:
        retrieval_query = (
            f"{query}\n\nRecent conversation:\n{conversation_context}"
        )

    # search_documents now returns structured source objects
    sources = search_documents(user.id, retrieval_query)

    if not sources:
        answer = "No relevant document found."
        api_sources = []

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

        # Strip internal 'text' field — safe for API serialisation
        api_sources = _strip_text_field(sources[:5])

    query_counts[user.email] = query_counts.get(user.email, 0) + 1

    history = History(
        query=query,
        answer=answer,
        user_id=user.id
    )
    db.add(history)

    return {"answer": answer, "sources": api_sources}