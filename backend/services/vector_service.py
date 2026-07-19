import chromadb
import re
import math
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


def build_source_object(doc, meta, distance=None):
    """
    Build a structured source citation object from a ChromaDB result.

    Returns a dict with:
      - filename   : source document name
      - chunk_index: which chunk within the document
      - score      : float [0, 1] derived from L2 distance, or None if unavailable
      - preview    : truncated text for UI display (≤ 200 chars)
      - text       : full raw chunk text used to build the LLM context string
                     (stripped before returning to the API layer)
    """
    filename = meta.get("filename", "Unknown document")
    chunk_index = meta.get("chunk_index", 0)

    score = None
    if isinstance(distance, (int, float)):
        # Convert L2 distance into intuitive confidence percentage [0, 1]
        score = round(1.0 / (1.0 + distance), 4)

    full_text = (doc or "").strip()
    preview = full_text[:200]
    if len(full_text) > 200:
        preview = preview.rstrip() + "..."

    return {
        "filename": filename,
        "chunk_index": chunk_index,
        "score": score,
        "preview": preview,
        "text": full_text,  # internal only — stripped by caller before API response
    }


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
        "metadatas": [],
        "embeddings": []
    }

    for value in user_id_values(user_id):
        result = collection.get(
            where={
                "user_id": value
            },
            include=include or ["documents", "metadatas"]
        )

        for key in chunks:
            if key in result and result[key] is not None:
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


def expand_query(query):
    """
    Automatically expand user query with synonyms/related keywords using Groq.
    """
    from services.llm_service import client as groq_client
    if not groq_client:
        return query
    try:
        prompt = f"""You are a search query optimizer for an enterprise search system.
Extract the core entities and add 1-2 STRICT synonyms for the following user query to improve retrieval. 
If the query is a person's name, a specific file name, or a specific title, DO NOT add any extra terms, do not guess their identity, and do not add generic industry words.
Do not return any explanations, punctuation, or preamble. Return only the space-separated list of keywords.

Query: {query}
Keywords:"""
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=50
        )
        expanded_keywords = response.choices[0].message.content.strip()
        print(f"Original Query: '{query}' -> Expanded Keywords: '{expanded_keywords}'")
        return f"{query} {expanded_keywords}"
    except Exception as e:
        print("Query expansion error:", e)
        return query


def calculate_bm25_scores(query_text, documents):
    """
    Compute BM25 scores for a list of documents relative to the query text.
    """
    def get_tokens(text):
        return re.findall(r"[a-z0-9]+", (text or "").lower())

    query_tokens = [t for t in get_tokens(query_text) if len(t) > 1]
    if not query_tokens:
        return [0.0] * len(documents)

    N = len(documents)
    if N == 0:
        return []

    doc_tokens_lists = [get_tokens(doc) for doc in documents]
    doc_lengths = [len(tokens) for tokens in doc_tokens_lists]
    avgdl = sum(doc_lengths) / N if N > 0 else 1.0

    # Calculate doc term frequencies
    doc_tfs = []
    for tokens in doc_tokens_lists:
        tf = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        doc_tfs.append(tf)

    # Calculate n(q)
    nq = {}
    for token in query_tokens:
        nq[token] = sum(1 for tf in doc_tfs if token in tf)

    # Calculate IDF
    idf = {}
    for token in query_tokens:
        count = nq[token]
        idf[token] = math.log((N - count + 0.5) / (count + 0.5) + 1.0)

    # Calculate scores
    k1 = 1.5
    b = 0.75
    scores = []
    for idx, tf in enumerate(doc_tfs):
        score = 0.0
        doc_len = doc_lengths[idx]
        for token in query_tokens:
            if token in tf:
                freq = tf[token]
                num = freq * (k1 + 1)
                den = freq + k1 * (1 - b + b * (doc_len / avgdl))
                score += idf[token] * (num / den)
        scores.append(score)
    return scores


def search_documents(user_id, query, limit=5):
    """
    Perform hybrid search (Chroma + BM25) and fuse results using RRF.
    Return top 5 non-duplicate relevant chunks.
    """
    cleaned_query = clean_text(query)
    if not cleaned_query:
        return []

    total_vectors = collection.count()
    if total_vectors == 0:
        return []

    # 1. Query Expansion
    expanded_query = expand_query(cleaned_query)

    # 2. Vector Search (using original query embedding for semantic match)
    query_embedding = get_embedding_model().encode([cleaned_query]).tolist()[0]
    
    # Fetch top 50 from vector search to have a rich pool for fusion
    requested_results = min(50, total_vectors)
    
    chroma_candidates = []
    seen_ids = set()
    for value in user_id_values(user_id):
        current_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=requested_results,
            where={
                "user_id": value
            },
            include=["documents", "metadatas", "distances", "embeddings"]
        )

        current_docs = current_results.get("documents", [[]])[0]
        current_metas = current_results.get("metadatas", [[]])[0]
        current_distances = current_results.get("distances", [[]])[0]
        current_ids = current_results.get("ids", [[]])[0]
        current_embs = current_results.get("embeddings", [[]])[0] if "embeddings" in current_results else [None] * len(current_docs)

        for index, doc in enumerate(current_docs):
            vector_id = current_ids[index] if index < len(current_ids) else None
            if not vector_id or vector_id in seen_ids:
                continue

            seen_ids.add(vector_id)
            chroma_candidates.append({
                "id": vector_id,
                "doc": doc,
                "meta": current_metas[index] if index < len(current_metas) else {},
                "distance": current_distances[index] if index < len(current_distances) else None,
                "embedding": current_embs[index] if index < len(current_embs) else None
            })

    # 3. Lexical Search (BM25 using expanded query)
    user_chunks = get_user_chunks(user_id, include=["documents", "metadatas", "embeddings"])
    all_docs = user_chunks.get("documents", [])
    all_metas = user_chunks.get("metadatas", [])
    all_ids = user_chunks.get("ids", [])
    all_embeddings = user_chunks.get("embeddings", [])

    bm25_scores = calculate_bm25_scores(expanded_query, all_docs)
    
    bm25_candidates = []
    for idx in range(len(all_docs)):
        score = bm25_scores[idx]
        if score > 0:
            bm25_candidates.append({
                "id": all_ids[idx],
                "doc": all_docs[idx],
                "meta": all_metas[idx],
                "bm25_score": score,
                "embedding": all_embeddings[idx] if idx < len(all_embeddings) else None
            })
    
    bm25_candidates = sorted(bm25_candidates, key=lambda x: x["bm25_score"], reverse=True)

    # 4. Reciprocal Rank Fusion (RRF)
    rrf_scores = {}
    k = 60

    # Rank chroma results
    for rank_idx, cand in enumerate(chroma_candidates):
        rrf_scores[cand["id"]] = rrf_scores.get(cand["id"], 0.0) + (1.0 / (k + (rank_idx + 1)))

    # Rank BM25 results
    for rank_idx, cand in enumerate(bm25_candidates):
        rrf_scores[cand["id"]] = rrf_scores.get(cand["id"], 0.0) + (1.0 / (k + (rank_idx + 1)))

    # Combine candidates
    id_to_cand = {}
    for cand in chroma_candidates:
        id_to_cand[cand["id"]] = cand
    for cand in bm25_candidates:
        if cand["id"] not in id_to_cand:
            id_to_cand[cand["id"]] = cand

    combined_candidates = []
    for cid, rrf_score in rrf_scores.items():
        cand = id_to_cand[cid]
        dist = cand.get("distance")
        
        # Performance: Reuse stored embedding to calculate distance for BM25 candidates that weren't in Chroma results
        if dist is None and cand.get("embedding") is not None:
            dist = sum((x - y) ** 2 for x, y in zip(query_embedding, cand["embedding"]))
        elif dist is None:
            dist = 1.0  # Safe fallback if embedding is missing
            
        combined_candidates.append({
            "id": cid,
            "doc": cand["doc"],
            "meta": cand["meta"],
            "rrf_score": rrf_score,
            "distance": dist
        })

    # Sort by RRF score descending
    combined_candidates = sorted(combined_candidates, key=lambda x: x["rrf_score"], reverse=True)

    # 5. Remove duplicate chunks
    unique_candidates = []
    seen_contents = set()
    for cand in combined_candidates:
        normalized_content = " ".join(cand["doc"].split()).lower()
        if normalized_content in seen_contents:
            continue
        seen_contents.add(normalized_content)
        unique_candidates.append(cand)

    # 6. Keep only top limit (5) and build source objects
    final_sources = [
        build_source_object(cand["doc"], cand["meta"], cand["distance"])
        for cand in unique_candidates[:limit]
    ]

    # 7. Filter out low-relevance chunks that are not meaningfully related
    #    to the query. Without this, every query returns top-5 even when
    #    none of the user's documents are relevant (e.g. asking about
    #    "Leave Policy" when only resumes/certificates are uploaded).
    MIN_RELEVANCE_SCORE = 0.38
    final_sources = [
        s for s in final_sources
        if s["score"] is not None and s["score"] >= MIN_RELEVANCE_SCORE
    ]

    return final_sources
