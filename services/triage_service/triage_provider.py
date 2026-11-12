from google.genai import types

from providers.gemini.client import GeminiClient
from schemas.triage import TriageResult
from services.triage_service.safety_rules import SafetyRuleEngine


class TriageProvider:
    """
    Evaluates clinical urgency for patient cases by combining:
    1. Deterministic regex-based red-flag scanning (instant, no API call).
    2. Gemini structured classification for nuanced urgency assessment.
    """

    def __init__(self, gemini_client: GeminiClient | None = None):
        self.gemini_client = gemini_client or GeminiClient()

    async def evaluate_triage(
        self,
        structured_prompt: str,
        is_medical: bool = True,
    ) -> TriageResult:

        # Non-medical queries exit immediately
        if not is_medical:
            return TriageResult(
                is_medical=False,
                is_emergency=False,
                urgency_level="non_medical",
                flags=[],
                reasoning="The input does not contain a medical concern.",
                emergency_guidance=None,
            )

        # Step 1: Deterministic red-flag scan (no LLM needed)
        deterministic_flags = SafetyRuleEngine.scan_for_red_flags(structured_prompt)

        if deterministic_flags:
            return TriageResult(
                is_medical=True,
                is_emergency=True,
                urgency_level="emergency",
                flags=deterministic_flags,
                reasoning="Immediate life-threatening or high-risk red flag detected by safety rules.",
                emergency_guidance=(
                    "EMERGENCY ALERT: Potential life-threatening symptoms detected. "
                    "Please call emergency services (911 / 112 / your local emergency number) "
                    "or proceed immediately to the nearest emergency department. "
                    "Do not drive yourself."
                ),
            )

        # Step 2: LLM-based structured triage for non-obvious cases
        system_prompt = """
You are a medical triage decision system.
Analyze the user's clinical situation and classify urgency level:
- "emergency": Potentially life-threatening or rapidly deteriorating conditions requiring immediate ER care.
- "urgent": Conditions requiring prompt medical attention within 24-48 hours (e.g. high fever with lethargy, severe acute pain, spreading infection).
- "routine": Non-acute symptoms, general wellness, chronic disease checkups, minor rash, mild cough.
- "non_medical": General conversational questions unrelated to health.

Rules:
- Be conservative: if symptoms could reasonably indicate a severe condition, classify as "emergency" or "urgent".
- Provide clear reasoning.
- If emergency, provide direct guidance to call emergency services.
"""

        prompt = f"""
{system_prompt}

Patient Case:
{structured_prompt}
"""

        response = await self.gemini_client.generate_content(
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TriageResult.model_json_schema(),
            ),
        )

        return TriageResult.model_validate_json(response.text)

