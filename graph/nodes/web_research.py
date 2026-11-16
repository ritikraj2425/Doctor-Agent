import logging
from graph.state import DoctorAgentState
from providers.web.search import TavilyWebSearchProvider


class WebResearchNode:

    def __init__(self, search_provider: TavilyWebSearchProvider):
        self.search_provider = search_provider

    async def __call__(
        self,
        state: DoctorAgentState,
    ) -> dict:

        try:
            results = await self.search_provider.search(state["structured_prompt"])
        except Exception:
            logging.getLogger(__name__).exception("Web research failed")
            return {"web_results": [], "web_research_error": "Web search is temporarily unavailable."}

        if isinstance(results, dict):
            results = results.get("results", [])
        elif not isinstance(results, list):
            results = []

        return {
            "web_results": results,
        }
