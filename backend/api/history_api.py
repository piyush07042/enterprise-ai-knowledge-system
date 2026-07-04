from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth.dependencies import verify_token
from database.db import get_db
from models.history import History

router = APIRouter()


@router.get("/history")
def get_history(
    user=Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        items = db.query(History).filter(
            History.user_id == user.id
        ).all()

        result = []
        for item in items:
            result.append({
                "id": item.id,
                "query": item.query,
                "answer": item.answer
            })

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))