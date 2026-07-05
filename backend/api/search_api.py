from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth.dependencies import verify_token
import traceback

from database.db import get_db
from sqlalchemy.orm import Session
from services.search_service import answer_from_documents

router = APIRouter()


class SearchRequest(BaseModel):
    query: str


@router.post("/search")
def search(
    request: SearchRequest,
    user=Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        print("========== SEARCH START ==========")
        print("USER ID:", user.id)
        print("QUERY:", request.query)

        answer = answer_from_documents(user, db, request.query)
        db.commit()

        print("ANSWER GENERATED")
        print("========== SEARCH END ==========")

        return {"answer": answer}

    except Exception as e:
        print("SEARCH ERROR:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
