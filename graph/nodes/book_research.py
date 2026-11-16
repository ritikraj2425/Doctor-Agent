import logging
from graph.state import DoctorAgentState
from services.retrieval_service.book_retriever import BookRetriever

class BookResearchNode:

    def __init__(self, retriever: BookRetriever):
        self.retrieval = retriever

    async def __call__(
        self,
        state: DoctorAgentState,
    ) -> dict:

        try:
            results = await self.retrieval.search(query=state["structured_prompt"], k=5)
        except Exception:
            logging.getLogger(__name__).exception("Medical reference retrieval failed")
            return {"book_results": [], "book_research_error": "Medical reference search is temporarily unavailable."}

        return {
            "book_results": results
        }
