from graph.state import DoctorAgentState


class EmergencyResponseNode:
    """
    Constructs an immediate emergency advisory when critical red flags
    are detected during triage, bypassing the slower research pipeline.
    """

    async def __call__(
        self,
        state: DoctorAgentState,
    ) -> dict:

        triage_data = state.get("triage", {})

        emergency_guidance = triage_data.get("emergency_guidance") or (
            "EMERGENCY WARNING: Critical symptoms have been detected in your description. "
            "Please seek immediate emergency medical care (call 911 / 112 or visit the nearest "
            "hospital emergency room immediately). Do not delay."
        )

        reasoning = triage_data.get("reasoning", "High-risk clinical symptoms detected.")

        flags = triage_data.get("flags", [])
        flag_details = ""
        for f in flags:
            flag_details += f"\n- **[{f.get('category', 'general').upper()}]** {f.get('flag', '')}"

        emergency_summary = (
            f"⚠️ **EMERGENCY MEDICAL ESCALATION**\n\n"
            f"{emergency_guidance}\n\n"
            f"**Triage Reason:** {reasoning}\n\n"
        )

        if flag_details:
            emergency_summary += f"**Detected Red Flags:**{flag_details}\n\n"

        emergency_summary += (
            f"**Immediate Recommended Actions:**\n"
            f"1. Call local emergency medical services immediately.\n"
            f"2. Stay calm and rest in a comfortable position.\n"
            f"3. Do not attempt to drive yourself to the hospital.\n"
            f"4. If accompanied, inform the person near you about your symptoms."
        )

        return {
            "final_response": emergency_summary,
            "response": emergency_summary,
            "is_emergency": True,
            "urgency_level": "emergency",
        }

