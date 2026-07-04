import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path="chroma_db")

collection = client.get_or_create_collection(
    name="documents"
)

model = SentenceTransformer("all-MiniLM-L6-v2")


def store_document(user_id, filename, text):
    chunks = []
    chunk_size = 500

    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])

    if not chunks:
        return

    embeddings = model.encode(chunks).tolist()

    ids = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        ids.append(f"{user_id}_{filename}_{i}")
        metadatas.append({
            "user_id": str(user_id),
            "filename": filename
        })

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas
    )


def delete_document_chunks(user_id, filename):
    collection.delete(
        where={
            "user_id": str(user_id),
            "filename": filename,
        }
    )


def search_documents(user_id, query):
    query_embedding = model.encode([query]).tolist()[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    if not results["documents"]:
        return []

    docs = results["documents"][0]
    metas = results["metadatas"][0]

    filtered_docs = []

    for doc, meta in zip(docs, metas):
        if meta["user_id"] == str(user_id):
            filtered_docs.append(doc)

    return filtered_docs