from database.db import SessionLocal
from models.document import Document
from models.user import User
from services.document_sync_service import sync_user_upload_documents
from services.vector_service import get_embedding_model, store_document
import chromadb

get_embedding_model()

db = SessionLocal()

for user in db.query(User).all():
    sync_user_upload_documents(user, db, index_missing=False)

db.commit()

# Clear old vectors
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection(name="documents")

all_data = collection.get()
if all_data["ids"]:
    collection.delete(ids=all_data["ids"])

print("Old vectors cleared")

docs = db.query(Document).all()

for doc in docs:
    print("Indexing:", doc.filename)
    store_document(
        doc.user_id,
        doc.filename,
        doc.content
    )

print("Reindex complete")
db.close()
