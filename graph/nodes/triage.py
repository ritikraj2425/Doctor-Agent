from graph.state import DoctorAgentState
from services.triage_service.triage_provider import TriageProvider


class TriageNode:

    def __init__(self, triage_provider: TriageProvider):
        self.triage_provider = triage_provider

    async def __call__(
        self,
        state: DoctorAgentState,
    ) -> dict:

        structured_prompt = state.get("structured_prompt", "") or state.get("prompt", "")
        is_medical = state.get("is_medical", True)

        triage_result = await self.triage_provider.evaluate_triage(
            structured_prompt=structured_prompt,
            is_medical=is_medical,
        )

        return {
            "triage": triage_result.model_dump(),
            "is_emergency": triage_result.is_emergency,
            "urgency_level": triage_result.urgency_level,
        }

