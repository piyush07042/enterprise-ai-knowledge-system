from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth.dependencies import verify_token
from services.vector_service import search_documents
from services.llm_service import generate_answer
from api.stats_api import query_counts
from api.stats_api import query_counts
import traceback

from database.db import get_db
from sqlalchemy.orm import Session
from models.history import History

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

        docs = search_documents(user.id, request.query)

        print("DOCS FOUND:", len(docs))

        if not docs:
            return {"answer": "No relevant document found."}

        context = "\n\n".join(docs[:5])

        answer = generate_answer(context, request.query)

        # stats
        query_counts[user.email] = query_counts.get(user.email, 0) + 1

        # save history
        history = History(
            query=request.query,
            answer=answer,
            user_id=user.id
        )

        db.add(history)
        db.commit()

        print("ANSWER GENERATED")
        print("========== SEARCH END ==========")

        return {"answer": answer}

    except Exception as e:
        print("SEARCH ERROR:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))