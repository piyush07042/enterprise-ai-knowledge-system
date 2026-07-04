from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.dependencies import verify_token
from auth.security import hash_password
from database.db import get_db
from models.user import User

router = APIRouter()


@router.get("/settings")
def get_settings(user=Depends(verify_token)):
    return {
        "username": user.username,
        "email": user.email
    }


@router.put("/settings")
def update_settings(
    data: dict,
    user=Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if email and email != user.email:
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="Email already exists"
                )
            user.email = email

        if username:
            user.username = username

        if password:
            user.password = hash_password(password)

        db.commit()
        db.refresh(user)

        return {"message": "Profile updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))