from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.dependencies import verify_token
from database.db import get_db
from services.search_service import answer_from_documents

router = APIRouter()


@router.post("/chat")
def chat(
    data: dict,
    user=Depends(verify_token),
    db: Session = Depends(get_db),
):
    question = data.get("question", "")

    result = answer_from_documents(
        user=user,
        db=db,
        query=question,
    )

    db.commit()

    return result