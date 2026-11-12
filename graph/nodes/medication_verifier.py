from graph.state import DoctorAgentState
from services.medication_service.medication_verifier import MedicationVerifier


class MedicationVerifierNode:

    def __init__(self, medication_verifier: MedicationVerifier):
        self.medication_verifier = medication_verifier

    async def __call__(
        self,
        state: DoctorAgentState,
    ) -> dict:

        structured_prompt = state.get("structured_prompt", "")
        differential = state.get("differential")

        med_result = await self.medication_verifier.verify_medications(
            structured_prompt=structured_prompt,
            differential_summary=differential,
        )

        return {
            "medication_check": med_result.model_dump(),
            "medicines": [m.model_dump() for m in med_result.medicines_identified],
        }

