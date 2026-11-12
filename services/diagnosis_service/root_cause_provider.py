import json

from google.genai import types

from providers.gemini.client import GeminiClient
from schemas.diagnosis import DifferentialAnalysis


class RootCauseProvider:
    """
    Synthesizes patient context and dual-source research findings
    (medical textbook RAG + trusted web) into a structured differential
    diagnosis with conservative care guidance.
    """

    def __init__(self, gemini_client: GeminiClient | None = None):
        self.gemini_client = gemini_client or GeminiClient()

    async def generate_differential(
        self,
        structured_prompt: str,
        web_results: list[dict],
        book_results: list[dict],
    ) -> DifferentialAnalysis:

        system_prompt = """
You are a senior clinical decision support specialist performing a differential diagnosis synthesis.

Your task:
1. Synthesize the user's clinical context with findings from authoritative medical textbooks and trusted web sources.
2. Formulate 2 to 4 ranked differential possibilities (high, moderate, or low likelihood).
3. Clearly state corroborating and conflicting evidence for each possibility.
4. Provide safe, conservative, non-pharmacological care and monitoring steps (e.g. hydration, rest, symptom journaling).
5. Prepare thoughtful, specific questions the patient should ask their doctor during an appointment.
6. List warning signs (red flags) that should prompt urgent evaluation.

Rules:
- Never declare a diagnosis with 100% certainty. Use probabilistic clinical language.
- Do not prescribe prescription drugs or advise altering prescription regimens.
- Rely strictly on evidence from the provided medical sources.
- If the evidence is insufficient to identify a condition, explicitly say so.
"""

        prompt = f"""
{system_prompt}

USER CLINICAL CONTEXT:
{structured_prompt}

AUTHORITATIVE MEDICAL TEXTBOOK FINDINGS:
{json.dumps(book_results, ensure_ascii=False, indent=2)}

TRUSTED WEB RESEARCH FINDINGS:
{json.dumps(web_results, ensure_ascii=False, indent=2)}
"""

        response = await self.gemini_client.generate_content(
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=DifferentialAnalysis.model_json_schema(),
                temperature=0.2,
            ),
        )

        return DifferentialAnalysis.model_validate_json(response.text)

