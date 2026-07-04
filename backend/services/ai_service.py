
import re

# In-memory storage instead of ChromaDB
documents_store = []


def store_document(document_id, filename, text, user_email):
    documents_store.append({
        "document_id": document_id,
        "filename": filename,
        "content": text,
        "user_email": user_email
    })


def search_documents(query, user_email):
    query = query.lower()
    results = []

    ignore_words = [
        "what", "is", "about", "the", "a", "an",
        "in", "on", "of", "written", "tell", "me",
        "who", "signed", "form", "which", "are"
    ]

    cleaned_query = re.sub(r'[^a-z0-9]', ' ', query)

    keywords = [
        word for word in cleaned_query.split()
        if word not in ignore_words
    ]

    for doc in documents_store:
        if doc["user_email"] != user_email:
            continue

        filename = doc["filename"].lower()
        content = doc["content"].lower()

        # filename match
        if keywords and all(word in filename for word in keywords):
            results.append({
                "document_id": doc["document_id"],
                "filename": doc["filename"],
                "preview": doc["content"][:500],
                "score": 0
            })
            continue

        # content match
        if keywords and all(word in content for word in keywords):
            results.append({
                "document_id": doc["document_id"],
                "filename": doc["filename"],
                "preview": doc["content"][:500],
                "score": 1
            })

    return results


def delete_document_vectors(document_id):
    global documents_store
    documents_store = [
        doc for doc in documents_store
        if doc["document_id"] != document_id
    ]
