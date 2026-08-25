from graph.state import DoctorAgentState
from services.context_service.context_provider import ContextProvider


class UnderstandContextNode:

    def __init__(self, context_provider: ContextProvider):
        self.context_provider = context_provider

    async def __call__(
        self,
        state: DoctorAgentState,
    ) -> dict:

        context = await self.context_provider.process(
            file_path=state.get("file_path"),
            prompt=state["prompt"],
            file_type=state.get("file_type"),
        )

        return {
            "is_medical": context.is_medical,
            "structured_prompt": context.structured_prompt,
            "response": context.response,
        }