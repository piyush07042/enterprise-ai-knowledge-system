from pathlib import Path

from models.document import Document
from services.pdf_service import extract_pdf_text
from services.vector_service import delete_document_chunks, store_document
from utils.file_paths import resolve_user_upload_path, sanitize_filename


def extract_file_text(file_path, filename):
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        return extract_pdf_text(file_path)

    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8")

    return filename


def sync_user_upload_documents(user, db, base_folder="uploads", index_missing=True):
    user_folder = Path(base_folder) / user.email

    if not user_folder.exists():
        db.query(Document).filter(Document.user_id == user.id).delete()
        db.flush()
        return []

    synced_documents = []
    disk_filenames = set()

    for file_path in sorted(user_folder.iterdir()):
        if not file_path.is_file():
            continue

        filename = sanitize_filename(file_path.name)
        disk_filenames.add(filename)
        safe_file_path = resolve_user_upload_path(base_folder, user.email, filename)

        document = db.query(Document).filter(
            Document.user_id == user.id,
            Document.filename == filename
        ).first()

        if document is None:
            text = extract_file_text(safe_file_path, filename)
            document = Document(
                filename=filename,
                content=text,
                user_id=user.id
            )
            db.add(document)
            db.flush()

            if index_missing:
                store_document(user.id, filename, text)
        elif not document.content:
            text = extract_file_text(safe_file_path, filename)
            document.content = text

            if index_missing:
                delete_document_chunks(user.id, filename)
                store_document(user.id, filename, text)

        synced_documents.append(document)

    # Sync deletions (delete from DB if not on disk)
    db_documents = db.query(Document).filter(Document.user_id == user.id).all()
    for db_doc in db_documents:
        if db_doc.filename not in disk_filenames:
            delete_document_chunks(user.id, db_doc.filename)
            db.delete(db_doc)
    db.flush()

    return synced_documents
