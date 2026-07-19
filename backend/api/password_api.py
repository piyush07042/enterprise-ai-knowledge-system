import os
import re
import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.security import hash_password, SECRET_KEY, ALGORITHM
from jose import jwt
from auth.dependencies import verify_token
from database.db import get_db, engine
from models.user import User
from models.password_otp import PasswordResetOTP

try:
    from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
    FASTAPI_MAIL_AVAILABLE = True
except Exception:
    FASTAPI_MAIL_AVAILABLE = False

router = APIRouter()


def _generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"


def _password_valid(password: str) -> bool:
    # basic strength: min 8, has letter and number
    if len(password) < 8:
        return False
    if not re.search(r"[A-Za-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    return True


def _send_email(to_email: str, subject: str, body: str):
    if not FASTAPI_MAIL_AVAILABLE:
        # fallback to console logging
        print(f"[MAIL] To: {to_email} Subject: {subject}\n{body}")
        return

    conf = ConnectionConfig(
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_FROM=os.getenv("MAIL_FROM", "no-reply@example.com"),
        MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "Enterprise AI"),
        MAIL_SERVER=os.getenv("MAIL_SERVER", "localhost"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 25)),
        MAIL_TLS=os.getenv("MAIL_TLS", "false").lower() in ("1", "true", "yes"),
        MAIL_SSL=os.getenv("MAIL_SSL", "false").lower() in ("1", "true", "yes"),
        USE_CREDENTIALS=bool(os.getenv("MAIL_USERNAME")),
        TEMPLATE_FOLDER="templates"
    )

    message = MessageSchema(
        subject=subject,
        recipients=[to_email],
        body=body,
        subtype="plain",
    )

    fm = FastMail(conf)
    try:
        # send asynchronously so endpoint returns quickly
        try:
            import asyncio

            asyncio.create_task(fm.send_message(message))
        except Exception:
            # fallback to synchronous send if event loop not available
            fm.send_message(message)
    except Exception as e:
        # don't raise to user; log instead
        print("Error sending mail:", e)


@router.post("/forgot-password")
def forgot_password(data: dict, db: Session = Depends(get_db)):
    email = (data.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Email address not registered"
        )

    otp = _generate_otp()
    expires = datetime.utcnow() + timedelta(minutes=5)

    # store OTP (one active per email)
    # remove existing
    db.query(PasswordResetOTP).filter(PasswordResetOTP.email == email).delete()
    record = PasswordResetOTP(email=email, otp=otp, expires_at=expires)
    db.add(record)
    db.commit()

    # send email
    subject = "Your password reset code"
    body = f"Your password reset code is: {otp}\nIt expires in 5 minutes."
    _send_email(email, subject, body)

    return {"message": "OTP sent successfully"}


@router.post("/verify-otp")
def verify_otp(data: dict, db: Session = Depends(get_db)):
    email = (data.get("email") or "").strip().lower()
    otp = (data.get("otp") or "").strip()

    if not email or not otp:
        raise HTTPException(status_code=400, detail="Email and OTP are required")

    record = db.query(PasswordResetOTP).filter(
        PasswordResetOTP.email == email,
        PasswordResetOTP.otp == otp,
    ).first()

    if not record:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if record.expires_at < datetime.utcnow():
        # delete expired
        db.delete(record)
        db.commit()
        raise HTTPException(status_code=400, detail="OTP expired")

    # success -> delete record and return short-lived reset token
    db.delete(record)
    db.commit()

    payload = {
        "sub": email,
        "pw_reset": True,
        "exp": datetime.utcnow() + timedelta(minutes=10)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return {"message": "OTP verified", "reset_token": token}


@router.post("/reset-password")
def reset_password(data: dict, db: Session = Depends(get_db)):
    reset_token = data.get("reset_token") or ""
    new_password = data.get("new_password") or ""

    if not reset_token or not new_password:
        raise HTTPException(status_code=400, detail="Reset token and new password are required")

    if not _password_valid(new_password):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters and include letters and numbers")

    try:
        payload = jwt.decode(reset_token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("pw_reset") or not payload.get("sub"):
            raise HTTPException(status_code=401, detail="Invalid reset token")
        email = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid request")

    user.password = hash_password(new_password)
    db.commit()

    return {"message": "Password reset successfully"}
