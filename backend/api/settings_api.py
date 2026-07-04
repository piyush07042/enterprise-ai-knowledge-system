import os
from pathlib import Path
import shutil

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from auth.dependencies import verify_token
from auth.security import hash_password, create_access_token
from database.db import get_db
from models.user import User
from utils.file_paths import (
    MAX_PROFILE_PICTURE_SIZE,
    get_profile_picture_folder,
    get_profile_picture_path,
    is_allowed_profile_picture,
)

router = APIRouter()
BASE_UPLOAD_FOLDER = "uploads"


def _clear_directory_except(directory: Path, keep_path: Path) -> None:
    if not directory.exists():
        return

    for entry in directory.iterdir():
        try:
            if entry.resolve() == keep_path.resolve():
                continue
        except FileNotFoundError:
            continue

        if entry.is_dir():
            shutil.rmtree(entry)
        else:
            entry.unlink(missing_ok=True)


def _profile_picture_url_for_user(user: User) -> str | None:
    return "/profile-picture" if user.profile_picture_path else None


@router.get("/settings")
def get_settings(user=Depends(verify_token)):
    return {
        "username": user.username,
        "email": user.email,
        "profile_picture_url": _profile_picture_url_for_user(user),
    }


@router.put("/settings")
def update_settings(
    data: dict,
    user=Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        old_email = user.email
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        access_token = None
        renamed_folders: list[tuple[Path, Path]] = []

        if email and email != user.email:
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="Email already exists"
                )
            old_doc_folder = Path(BASE_UPLOAD_FOLDER) / old_email
            new_doc_folder = Path(BASE_UPLOAD_FOLDER) / email
            if old_doc_folder.exists():
                os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)
                if new_doc_folder.exists():
                    raise HTTPException(
                        status_code=400,
                        detail="Target email folder already exists"
                    )
                os.rename(old_doc_folder, new_doc_folder)
                renamed_folders.append((old_doc_folder, new_doc_folder))

            old_picture_folder = get_profile_picture_folder(old_email)
            new_picture_folder = get_profile_picture_folder(email)
            if old_picture_folder.exists():
                new_picture_folder.parent.mkdir(parents=True, exist_ok=True)
                if new_picture_folder.exists():
                    raise HTTPException(
                        status_code=400,
                        detail="Target profile picture folder already exists"
                    )
                os.rename(old_picture_folder, new_picture_folder)
                renamed_folders.append((old_picture_folder, new_picture_folder))

            if user.profile_picture_path:
                picture_name = Path(user.profile_picture_path).name
                user.profile_picture_path = str(
                    get_profile_picture_path(email, picture_name)
                )

            user.email = email
            access_token = create_access_token({"sub": email})

        if username:
            user.username = username

        if password:
            user.password = hash_password(password)

        db.commit()
        db.refresh(user)

        response = {"message": "Profile updated successfully"}
        if access_token:
            response["access_token"] = access_token
            response["token_type"] = "bearer"
        return response

    except HTTPException:
        raise

    except Exception as e:
        for source_path, destination_path in reversed(renamed_folders):
            if destination_path.exists() and not source_path.exists():
                os.rename(destination_path, source_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    user=Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Profile picture file is required")

        if not is_allowed_profile_picture(file.filename, file.content_type):
            raise HTTPException(
                status_code=400,
                detail="Only JPG, JPEG and PNG images are allowed"
            )

        content = await file.read()
        if len(content) > MAX_PROFILE_PICTURE_SIZE:
            raise HTTPException(status_code=400, detail="Profile picture must be 2 MB or smaller")

        extension = Path(file.filename).suffix.lower()
        if extension == ".jpeg":
            extension = ".jpg"

        folder = get_profile_picture_folder(user.email)
        folder.mkdir(parents=True, exist_ok=True)

        previous_path = Path(user.profile_picture_path) if user.profile_picture_path else None
        new_path = folder / f"profile_picture{extension}"

        with open(new_path, "wb") as image_file:
            image_file.write(content)

        user.profile_picture_path = str(new_path)
        db.commit()
        db.refresh(user)

        _clear_directory_except(folder, new_path)
        if previous_path and previous_path != new_path and previous_path.exists():
            previous_path.unlink(missing_ok=True)

        return {
            "message": "Profile picture uploaded successfully",
            "profile_picture_url": "/profile-picture"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile-picture")
def get_profile_picture(user=Depends(verify_token)):
    try:
        if not user.profile_picture_path:
            raise HTTPException(status_code=404, detail="Profile picture not found")

        file_path = Path(user.profile_picture_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Profile picture not found")

        return FileResponse(file_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))