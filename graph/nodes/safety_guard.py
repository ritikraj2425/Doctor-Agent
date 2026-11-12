from graph.state import DoctorAgentState
from services.safety_service.safety_guard import SafetyGuard


class SafetyGuardNode:

    def __init__(self, safety_guard: SafetyGuard | None = None):
        self.safety_guard = safety_guard or SafetyGuard()

    async def __call__(
        self,
        state: DoctorAgentState,
    ) -> dict:

        summary_text = (
            state.get("final_response", "")
            or state.get("response", "")
            or ""
        )
        is_emergency = state.get("is_emergency", False)
        urgency_level = state.get("urgency_level", "routine")
        differential = state.get("differential")
        medication_check = state.get("medication_check")
        triage = state.get("triage")

        final_response, review = self.safety_guard.audit_response(
            summary_text=summary_text,
            is_emergency=is_emergency,
            urgency_level=urgency_level,
            differential=differential,
            medication_check=medication_check,
            triage=triage,
        )

        return {
            "safety_review": review.model_dump(),
            "final_structured_response": final_response.model_dump(),
            "final_response": final_response.summary,
        }

