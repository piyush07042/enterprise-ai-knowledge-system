
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import FileResponse
import os
from jose import jwt, JWTError
from auth.dependencies import verify_token
from auth.security import SECRET_KEY, ALGORITHM
from services.vector_service import store_document
from pypdf import PdfReader

router = APIRouter()

BASE_UPLOAD_FOLDER = "uploads"
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user=Depends(verify_token)
):
    try:
        user_folder = os.path.join(BASE_UPLOAD_FOLDER, user.email)
        os.makedirs(user_folder, exist_ok=True)

        file_path = os.path.join(user_folder, file.filename)

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
            text = file.filename

        store_document(user.id, file.filename, text)

        return {
            "message": "File uploaded successfully",
            "filename": file.filename
        }

    except Exception as e:
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

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-file/{filename}")
def delete_file(filename: str, user=Depends(verify_token)):
    try:
        file_path = os.path.join(
            BASE_UPLOAD_FOLDER,
            user.email,
            filename
        )

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        os.remove(file_path)

        return {"message": "File deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
