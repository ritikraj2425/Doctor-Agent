from graph.state import DoctorAgentState
from services.retrieval_service.book_retriever import BookRetriever

class BookResearchNode:

    def __init__(self, retriever: BookRetriever):
        self.retrieval = retriever

    async def __call__(
        self,
        state: DoctorAgentState,
    ) -> dict:

        results = await self.retrieval.search(
            query=state["structured_prompt"],
            k=5
        )

        return {
            "book_results": results
        }