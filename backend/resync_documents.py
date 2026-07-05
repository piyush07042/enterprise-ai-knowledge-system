from database.db import SessionLocal
from models.user import User
from services.document_sync_service import sync_user_upload_documents

db = SessionLocal()

users = db.query(User).all()

for user in users:
    print(f"Syncing {user.email}")
    sync_user_upload_documents(user, db)

db.commit()

print("Documents synced successfully.")