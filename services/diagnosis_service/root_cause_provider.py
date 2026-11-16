import json

from providers.groq.client import GroqClient
from schemas.diagnosis import DifferentialAnalysis
from services.diagnosis_service.prompt_context import compact_sources, compact_text


class RootCauseProvider:
    """
    Synthesizes patient context and dual-source research findings
    (medical textbook RAG + trusted web) into a structured differential
    diagnosis with conservative care guidance.
    """

    def __init__(self, groq_client: GroqClient | None = None):
        self.groq_client = groq_client or GroqClient()

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

        # Search providers can return full page contents. Keep the model input
        # below the configured Groq TPM budget while retaining all sources in
        # graph state for the live UI and final evidence links.
        compact_books = compact_sources(book_results, count=2, excerpt_chars=400)
        compact_web = compact_sources(web_results, count=2, excerpt_chars=400)
        context = compact_text(structured_prompt, 1000)

        return await self.groq_client.generate_structured(
            system_prompt=system_prompt,
            user_prompt=f"""USER CLINICAL CONTEXT:
{context}

AUTHORITATIVE MEDICAL TEXTBOOK FINDINGS:
{json.dumps(compact_books, ensure_ascii=False, separators=(',', ':'))}

TRUSTED WEB RESEARCH FINDINGS:
{json.dumps(compact_web, ensure_ascii=False, separators=(',', ':'))}""",
            schema=DifferentialAnalysis,
            temperature=0.2,
        )

