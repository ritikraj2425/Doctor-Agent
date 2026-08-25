from graph.state import DoctorAgentState
from providers.web.search import TavilyWebSearchProvider


class WebResearchNode:

    def __init__(self, search_provider: TavilyWebSearchProvider):
        self.search_provider = search_provider

    async def __call__(
        self,
        state: DoctorAgentState,
    ) -> dict:

        results = await self.search_provider.search(
            state["structured_prompt"]
        )

        return {
            "web_results": results,
        }