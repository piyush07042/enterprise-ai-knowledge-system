import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONIOENCODING"] = "utf-8"

from dotenv import load_dotenv
load_dotenv()

from services.vector_service import search_documents

print("\n--- Searching as user_id=1 for 'data engineering certificate' ---")
sources = search_documents("1", "data engineering certificate")
for i, s in enumerate(sources):
    print(f"  [{i}] {s['filename']} (chunk {s['chunk_index']}, score={s['score']})")

print("\n--- Searching as user_id=1 for 'Piyush Gupta' ---")
sources = search_documents("1", "Piyush Gupta")
for i, s in enumerate(sources):
    print(f"  [{i}] {s['filename']} (chunk {s['chunk_index']}, score={s['score']})")

print("\n--- Searching as user_id=1 for 'resume' ---")
sources = search_documents("1", "resume")
for i, s in enumerate(sources):
    print(f"  [{i}] {s['filename']} (chunk {s['chunk_index']}, score={s['score']})")
