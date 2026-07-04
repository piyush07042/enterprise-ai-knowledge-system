
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import FileResponse
import os
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from auth.dependencies import verify_token
from auth.security import SECRET_KEY, ALGORITHM
from database.db import get_db
from models.document import Document
from services.vector_service import store_document, delete_document_chunks
from utils.file_paths import resolve_user_upload_path, sanitize_filename
from pypdf import PdfReader

router = APIRouter()

BASE_UPLOAD_FOLDER = "uploads"
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user=Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        user_folder = os.path.join(BASE_UPLOAD_FOLDER, user.email)
        os.makedirs(user_folder, exist_ok=True)

        filename = sanitize_filename(file.filename)
        file_path = resolve_user_upload_path(BASE_UPLOAD_FOLDER, user.email, filename)

        existing_document = db.query(Document).filter(
            Document.user_id == user.id,
            Document.filename == filename
        ).first()

        previous_file_bytes = file_path.read_bytes() if file_path.exists() else None
        previous_content = existing_document.content if existing_document else None

        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        text = ""

        if file.filename.lower().endswith(".pdf"):
            reader = PdfReader(file_path)

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text

        elif file.filename.lower().endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            text = filename

        if existing_document:
            delete_document_chunks(user.id, filename)

        store_document(user.id, filename, text)

        if existing_document:
            existing_document.content = text
        else:
            db.add(
                Document(
                    filename=filename,
                    content=text,
                    user_id=user.id
                )
            )
        db.commit()

        return {
            "message": "File uploaded successfully",
            "filename": filename
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        if previous_content is not None:
            try:
                if previous_file_bytes is not None:
                    with open(file_path, "wb") as f:
                        f.write(previous_file_bytes)
                elif file_path.exists():
                    os.remove(file_path)
                if existing_document:
                    delete_document_chunks(user.id, filename)
                    store_document(user.id, filename, previous_content)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
def get_documents(user=Depends(verify_token)):
    try:
        user_folder = os.path.join(BASE_UPLOAD_FOLDER, user.email)

        if not os.path.exists(user_folder):
            return []

        files = os.listdir(user_folder)

        documents = []
        for i, filename in enumerate(files):
            documents.append({
                "id": i + 1,
                "filename": filename
            })

        return documents

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/open-file/{filename}")
def open_file(filename: str, token: str = Query(...)):
    try:
        filename = sanitize_filename(filename)
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")

        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")

        file_path = os.path.join(
            BASE_UPLOAD_FOLDER,
            email,
            filename
        )

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(file_path)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{filename}/preview")
def preview_file(
    filename: str,
    user=Depends(verify_token)
):
    try:
        file_path = resolve_user_upload_path(BASE_UPLOAD_FOLDER, user.email, filename)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(file_path)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-file/{filename}")
def delete_file(
    filename: str,
    user=Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        filename = sanitize_filename(filename)
        file_path = resolve_user_upload_path(BASE_UPLOAD_FOLDER, user.email, filename)
        document = db.query(Document).filter(
            Document.user_id == user.id,
            Document.filename == filename
        ).first()

        if not file_path.exists() and document is None:
            raise HTTPException(status_code=404, detail="File not found")

        if file_path.exists():
            os.remove(file_path)

        delete_document_chunks(user.id, filename)

        if document is not None:
            db.delete(document)
            db.commit()

        return {"message": "File deleted successfully"}

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
