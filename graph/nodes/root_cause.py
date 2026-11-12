from graph.state import DoctorAgentState
from services.diagnosis_service.root_cause_provider import RootCauseProvider


class RootCauseNode:

    def __init__(self, root_cause_provider: RootCauseProvider):
        self.root_cause_provider = root_cause_provider

    async def __call__(
        self,
        state: DoctorAgentState,
    ) -> dict:

        structured_prompt = state.get("structured_prompt", "")
        web_results = state.get("web_results", [])
        book_results = state.get("book_results", [])

        differential = await self.root_cause_provider.generate_differential(
            structured_prompt=structured_prompt,
            web_results=web_results,
            book_results=book_results,
        )

        return {
            "differential": differential.model_dump(),
            "possible_causes": [c.model_dump() for c in differential.possible_causes],
        }

