import json
import re

from providers.groq.client import GroqClient, ProviderFallbackError
from schemas.medication import MedicationCheckResult
from services.diagnosis_service.prompt_context import compact_text


class MedicationVerifier:
    """
    Identifies medications in patient context and differentials,
    normalizes brand names to generic active ingredients, checks
    Rx vs OTC status, and flags potential interactions,
    duplicate therapies, or contraindications.
    """

    def __init__(self, groq_client: GroqClient | None = None):
        self.groq_client = groq_client or GroqClient()

    @staticmethod
    def _is_rate_limited(error: Exception) -> bool:
        if isinstance(error, ProviderFallbackError) or getattr(error, "status_code", None) == 429:
            return True
        body = getattr(error, "body", None) or {}
        detail = body.get("error") if isinstance(body, dict) else None
        return isinstance(detail, dict) and detail.get("code") == "rate_limit_exceeded"

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

        context = compact_text(structured_prompt, 1000)
        differential = compact_text(
            json.dumps(differential_summary or {}, ensure_ascii=False, separators=(",", ":")),
            800,
        )

        try:
            return await self.groq_client.generate_structured(
                system_prompt=system_prompt,
                user_prompt=f"""PATIENT CONTEXT:
{context}

DIFFERENTIAL ANALYSIS CONTEXT:
{differential}""",
                schema=MedicationCheckResult,
                temperature=0.1,
            )
        except Exception as exc:
            if not self._is_rate_limited(exc):
                raise
            self.groq_client.last_provider = "local"
            mentioned = bool(re.search(
                r"\b(medicat\w*|medicine|drug|tablet|pill|capsule|dose|prescrib\w*|"
                r"acetaminophen|paracetamol|ibuprofen|aspirin|antibiotic|insulin)\b",
                structured_prompt,
                re.IGNORECASE,
            ))
            warning = ({
                "severity": "moderate",
                "warning_type": "precaution",
                "message": "Automated medicine safety review was unavailable because the model providers could not complete the request. No medicine or interaction has been verified; ask a pharmacist or clinician before starting, stopping, or combining medicines.",
            } if mentioned else [])
            return MedicationCheckResult(
                has_medication_mention=mentioned,
                medicines_identified=[],
                warnings=[warning] if warning else [],
                pharmacist_note="Automated medication verification was temporarily unavailable. If you take or are considering any medicine, confirm it with a licensed pharmacist or clinician.",
            )

