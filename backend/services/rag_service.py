from typing import List, Dict

from services.search_service import semantic_search
from services.llm_service import llm_service


class RAGService:
    """
    Retrieval-Augmented Generation Service
    """

    @staticmethod
    def ask_question(user_id: int, question: str) -> Dict:
        """
        Pipeline

        Question
            ↓
        Vector Search
            ↓
        Top Chunks
            ↓
        LLM
            ↓
        Answer
        """

        search_results = semantic_search(
            user_id=user_id,
            query=question,
            top_k=5
        )

        contexts: List[str] = []
        sources: List[str] = []

        if search_results:

            for result in search_results:

                if isinstance(result, dict):

                    contexts.append(
                        result.get("content", "")
                    )

                    filename = result.get("filename")

                    if filename and filename not in sources:
                        sources.append(filename)

        answer = llm_service.generate_answer(
            question=question,
            contexts=contexts
        )

        return {
            "question": question,
            "answer": answer,
            "sources": sources
        }


rag_service = RAGService()