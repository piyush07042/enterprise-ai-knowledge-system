from database.db import SessionLocal
from models.document import Document
from models.user import User
from services.ai_service import store_document
import chromadb

# Clear old vectors
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection(name="documents")

all_data = collection.get()
if all_data["ids"]:
    collection.delete(ids=all_data["ids"])

print("Old vectors cleared")

db = SessionLocal()

docs = db.query(Document).all()

for doc in docs:
    user = db.query(User).filter(User.id == doc.user_id).first()

    if user:
        print("Indexing:", doc.filename)
        store_document(
            doc.id,
            doc.filename,
            doc.content,
            user.email
        )

print("Reindex complete")