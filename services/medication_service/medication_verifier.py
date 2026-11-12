import json

from google.genai import types

from providers.gemini.client import GeminiClient
from schemas.medication import MedicationCheckResult


class MedicationVerifier:
    """
    Identifies medications in patient context and differentials,
    normalizes brand names to generic active ingredients, checks
    Rx vs OTC status, and flags potential interactions,
    duplicate therapies, or contraindications.
    """

    def __init__(self, gemini_client: GeminiClient | None = None):
        self.gemini_client = gemini_client or GeminiClient()

    async def verify_medications(
        self,
        structured_prompt: str,
        differential_summary: dict | None = None,
    ) -> MedicationCheckResult:

        system_prompt = """
You are a clinical pharmacology verification system.

Your task:
1. Identify any medications mentioned in the patient's context (current medications, past remedies, or treatments discussed).
2. For each medication:
   - Normalize brand/trade names (e.g. Tylenol, Crocin, Advil, Motrin) to the international generic name (e.g. Acetaminophen, Ibuprofen).
   - Identify the drug class (e.g. NSAID, Analgesic, Statin, Beta-blocker).
   - Determine if it requires a prescription (prescription_required: true/false).
   - Note standard indications and prominent contraindications.
3. Evaluate safety risks:
   - Duplicate therapy: Check if patient is taking multiple drugs of the same class (e.g. two NSAIDs).
   - High-risk combinations or contraindications based on patient's stated conditions or allergies.
4. If no medications are mentioned or relevant, return has_medication_mention=false with empty lists.

Safety Rules:
- NEVER prescribe or suggest starting prescription medications.
- NEVER recommend specific dosages.
- Always encourage confirmation with a licensed pharmacist or prescribing physician.
"""

        prompt = f"""
{system_prompt}

PATIENT CONTEXT:
{structured_prompt}

DIFFERENTIAL ANALYSIS CONTEXT:
{json.dumps(differential_summary or {}, ensure_ascii=False, indent=2)}
"""

        response = await self.gemini_client.generate_content(
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MedicationCheckResult.model_json_schema(),
                temperature=0.1,
            ),
        )

        return MedicationCheckResult.model_validate_json(response.text)

