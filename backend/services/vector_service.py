import chromadb
import re
from sentence_transformers import SentenceTransformer
from services.text_chunker import chunk_text

client = chromadb.PersistentClient(path="chroma_db")

collection = client.get_or_create_collection(
    name="documents"
)

model = None


def get_embedding_model():
    global model

    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")

    return model


def clean_text(text):
    return " ".join((text or "").split())


def tokenize(text):
    ignored_words = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
        "in", "is", "it", "me", "of", "on", "or", "pdf", "tell", "the",
        "to", "what", "which", "who", "with"
    }

    tokens = set()

    for token in re.findall(r"[a-z0-9]+", (text or "").lower()):
        if token in ignored_words or len(token) <= 1:
            continue

        tokens.add(token)

        if token.endswith("s") and len(token) > 3:
            tokens.add(token[:-1])

    return tokens


def format_result(doc, meta, distance=None):
    filename = meta.get("filename", "Unknown document")
    chunk_index = meta.get("chunk_index", 0)
    score_line = f"Distance: {distance:.4f}" if isinstance(distance, float) else "Distance: n/a"

    return (
        f"Source: {filename}\n"
        f"Chunk: {chunk_index}\n"
        f"{score_line}\n"
        f"Content:\n{doc}"
    )


def user_id_values(user_id):
    values = [user_id]

    try:
        int_user_id = int(user_id)
        values.append(int_user_id)
    except (TypeError, ValueError):
        pass

    str_user_id = str(user_id)
    values.append(str_user_id)

    unique_values = []
    for value in values:
        if value not in unique_values:
            unique_values.append(value)

    return unique_values


def get_user_chunks(user_id, include=None):
    chunks = {
        "ids": [],
        "documents": [],
        "metadatas": []
    }

    for value in user_id_values(user_id):
        result = collection.get(
            where={
                "user_id": value
            },
            include=include or ["documents", "metadatas"]
        )

        for key in chunks:
            chunks[key].extend(result.get(key, []))

    return chunks


def lexical_score(query_tokens, query_text, doc, meta):
    filename = (meta.get("filename") or "").lower()
    filename_stem = filename.rsplit(".", 1)[0]
    doc_text = (doc or "").lower()
    doc_tokens = tokenize(doc)
    filename_tokens = tokenize(filename)

    overlap = len(query_tokens.intersection(doc_tokens))
    filename_overlap = len(query_tokens.intersection(filename_tokens))
    score = overlap + (filename_overlap * 3)

    if filename and filename in query_text:
        score += 8
    elif filename_stem and filename_stem in query_text:
        score += 5

    if "project" in query_tokens:
        if "projects" in doc_text:
            score += 4
        if "engineered" in doc_text or "developed" in doc_text:
            score += 3

    return score


def store_document(user_id, filename, text):
    cleaned_text = clean_text(text)

    if not cleaned_text:
        return

    chunks = [
        chunk.strip()
        for chunk in chunk_text(cleaned_text, chunk_size=1200, overlap=250)
        if chunk.strip()
    ]

    if not chunks:
        return

    embeddings = get_embedding_model().encode(chunks).tolist()

    ids = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        ids.append(f"{user_id}_{filename}_{i}")
        metadatas.append({
            "user_id": int(user_id),
            "user_id_text": str(user_id),
            "user": int(user_id),
            "filename": filename,
            "chunk_index": i
        })

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas
    )


def delete_document_chunks(user_id, filename):
    for value in user_id_values(user_id):
        collection.delete(
            where={
                "$and": [
                    {"user_id": value},
                    {"filename": filename}
                ]
            }
        )


def search_documents(user_id, query, limit=8):
    cleaned_query = clean_text(query)

    if not cleaned_query:
        return []

    total_vectors = collection.count()

    if total_vectors == 0:
        return []

    query_embedding = get_embedding_model().encode([cleaned_query]).tolist()[0]
    requested_results = min(max(limit, 8), total_vectors)

    docs = []
    metas = []
    distances = []
    seen_vector_ids = set()

    for value in user_id_values(user_id):
        current_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=requested_results,
            where={
                "user_id": value
            },
            include=["documents", "metadatas", "distances"]
        )

        current_docs = current_results.get("documents", [[]])[0]
        current_metas = current_results.get("metadatas", [[]])[0]
        current_distances = current_results.get("distances", [[]])[0]
        current_ids = current_results.get("ids", [[]])[0]

        for index, doc in enumerate(current_docs):
            vector_id = current_ids[index] if index < len(current_ids) else None

            if vector_id and vector_id in seen_vector_ids:
                continue

            if vector_id:
                seen_vector_ids.add(vector_id)

            docs.append(doc)
            metas.append(current_metas[index] if index < len(current_metas) else {})
            distances.append(current_distances[index] if index < len(current_distances) else None)

    if not docs:
        return []

    query_text = cleaned_query.lower()
    query_tokens = tokenize(query_text)
    candidates = {}
    seen = set()

    for index, (doc, meta) in enumerate(zip(docs, metas)):
        if not doc:
            continue

        filename = meta.get("filename", "Unknown document")
        chunk_index = meta.get("chunk_index", index)
        key = (filename, chunk_index, doc[:120])

        if key in seen:
            continue

        seen.add(key)
        distance = distances[index] if index < len(distances) else None
        vector_score = 0

        if isinstance(distance, float):
            vector_score = max(0, 3 - distance)

        score = vector_score + lexical_score(query_tokens, query_text, doc, meta)
        candidates[key] = (score, doc, meta, distance)

    user_chunks = get_user_chunks(user_id)

    for doc, meta in zip(user_chunks.get("documents", []), user_chunks.get("metadatas", [])):
        if not doc:
            continue

        filename = meta.get("filename", "Unknown document")
        chunk_index = meta.get("chunk_index", 0)
        key = (filename, chunk_index, doc[:120])
        score = lexical_score(query_tokens, query_text, doc, meta)

        if score <= 0:
            continue

        if key not in candidates or candidates[key][0] < score:
            candidates[key] = (score, doc, meta, None)

    ranked_candidates = sorted(
        candidates.values(),
        key=lambda item: item[0],
        reverse=True
    )

    filtered_docs = [
        format_result(doc, meta, distance)
        for _, doc, meta, distance in ranked_candidates[:limit]
    ]

    return filtered_docs
