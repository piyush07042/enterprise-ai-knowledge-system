from fastapi import Depends, HTTPException
from auth.dependencies import verify_token


def verify_admin(user=Depends(verify_token)):
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return user