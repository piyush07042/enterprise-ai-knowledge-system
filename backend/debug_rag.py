"""
Diagnostic script to trace the RAG pipeline for "What is Leave Policy?"
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONIOENCODING"] = "utf-8"

from dotenv import load_dotenv
load_dotenv()

from services.vector_service import search_documents, get_user_chunks, collection
from services.search_service import _build_rag_context
from services.llm_service import generate_answer, client as groq_client

# Step 1: Check what's in ChromaDB
print("=" * 60)
print("STEP 1: ChromaDB contents")
print("=" * 60)
data = collection.get(include=["documents", "metadatas"])
print(f"Total vectors in DB: {len(data['ids'])}")

# Group by user_id
users = {}
for i, meta in enumerate(data["metadatas"]):
    uid = meta.get("user_id", "unknown")
    if uid not in users:
        users[uid] = []
    users[uid].append({
        "id": data["ids"][i],
        "filename": meta.get("filename", "?"),
        "chunk_index": meta.get("chunk_index", 0),
        "doc_preview": (data["documents"][i] or "")[:100]
    })

for uid, chunks in users.items():
    print(f"\nUser ID: {uid} (type={type(uid).__name__}) -- {len(chunks)} chunks")
    filenames = set(c["filename"] for c in chunks)
    for fn in filenames:
        fn_chunks = [c for c in chunks if c["filename"] == fn]
        print(f"  FILE {fn}: {len(fn_chunks)} chunks")
        for c in fn_chunks[:2]:
            preview = c['doc_preview'].encode('ascii', errors='replace').decode('ascii')
            print(f"      chunk {c['chunk_index']}: {preview}...")

# Step 2: Test search for a specific user
print("\n" + "=" * 60)
print("STEP 2: Search results for 'What is Leave Policy?'")
print("=" * 60)

# Try all user IDs found
for uid in users:
    print(f"\n--- Searching as user_id={uid} ---")
    sources = search_documents(uid, "What is Leave Policy?")
    print(f"  Found {len(sources)} sources")
    for i, s in enumerate(sources):
        print(f"  [{i}] {s['filename']} (chunk {s['chunk_index']}, score={s['score']})")
        preview_safe = s['preview'][:120].encode('ascii', errors='replace').decode('ascii')
        print(f"       preview: {preview_safe}")
        print(f"       text length: {len(s.get('text', ''))}")
    
    if sources:
        # Step 3: Build context and check what the LLM receives
        print(f"\n--- Building RAG context ---")
        context = _build_rag_context(sources[:5])
        print(f"  Context length: {len(context)} chars")
        context_safe = context[:500].encode('ascii', errors='replace').decode('ascii')
        print(f"  Context preview (first 500 chars):")
        print(f"  {context_safe}")
        
        # Step 4: Check LLM
        print(f"\n--- Groq client status ---")
        print(f"  Client is None: {groq_client is None}")
        
        if groq_client is not None:
            print(f"\n--- Calling generate_answer ---")
            answer = generate_answer(context, "What is Leave Policy?")
            print(f"  Answer length: {len(answer)}")
            answer_safe = answer[:500].encode('ascii', errors='replace').decode('ascii')
            print(f"  Answer: {answer_safe}")
        else:
            print("  WARNING: Groq client is None -- LLM not available!")
        
        break  # Only test first user with results
    
print("\n" + "=" * 60)
print("STEP 3: Search results for 'describe my resume'")
print("=" * 60)

for uid in users:
    print(f"\n--- Searching as user_id={uid} ---")
    sources = search_documents(uid, "describe my resume")
    print(f"  Found {len(sources)} sources")
    for i, s in enumerate(sources):
        print(f"  [{i}] {s['filename']} (chunk {s['chunk_index']}, score={s['score']})")
        preview_safe = s['preview'][:120].encode('ascii', errors='replace').decode('ascii')
        print(f"       preview: {preview_safe}")
    
    if sources:
        context = _build_rag_context(sources[:5])
        print(f"\n  Context length: {len(context)} chars")
        
        if groq_client is not None:
            print(f"\n--- Calling generate_answer ---")
            answer = generate_answer(context, "describe my resume")
            print(f"  Answer length: {len(answer)}")
            answer_safe = answer[:500].encode('ascii', errors='replace').decode('ascii')
            print(f"  Answer: {answer_safe}")
    break
