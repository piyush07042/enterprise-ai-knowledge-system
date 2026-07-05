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
        return []

    synced_documents = []

    for file_path in sorted(user_folder.iterdir()):
        if not file_path.is_file():
            continue

        filename = sanitize_filename(file_path.name)
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

    return synced_documents
