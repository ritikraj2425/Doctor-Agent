import json

from graph.state import DoctorAgentState
from providers.groq.client import GroqClient, ProviderFallbackError
from services.diagnosis_service.prompt_context import compact_text


class SynthesisNode:

    def __init__(self):
        self.groq = GroqClient()

    @staticmethod
    def _is_rate_limited(error: Exception) -> bool:
        if isinstance(error, ProviderFallbackError) or getattr(error, "status_code", None) == 429:
            return True
        body = getattr(error, "body", None) or {}
        detail = body.get("error") if isinstance(body, dict) else None
        return isinstance(detail, dict) and detail.get("code") == "rate_limit_exceeded"

    @staticmethod
    def _fallback_response(differential: dict) -> str:
        """Turn completed analysis into a safe answer without another model call."""
        parts = [
            "The primary model was rate-limited and the Gemini fallback was unavailable. "
            "Here is a concise summary from the analysis already completed.",
        ]
        impression = differential.get("primary_impression")
        if impression:
            parts.extend(["", str(impression)])
        causes = differential.get("possible_causes") or []
        if causes:
            parts.extend(["", "Possibilities to discuss with a clinician:"])
            for cause in causes[:4]:
                if not isinstance(cause, dict):
                    continue
                name = cause.get("name", "Possible cause")
                likelihood = cause.get("likelihood")
                explanation = cause.get("explanation")
                label = f" ({likelihood} likelihood)" if likelihood else ""
                parts.append(f"• {name}{label}" + (f" — {explanation}" if explanation else ""))
        care_steps = [
            step for step in differential.get("care_steps", [])[:5]
            if isinstance(step, dict)
            and not any(word in f"{step.get('title', '')} {step.get('instructions', '')}".lower()
                        for word in ("medication", "medicine", "drug", "tablet", "dose", "prescription", "acetaminophen", "ibuprofen"))
        ]
        if care_steps:
            parts.extend(["", "Supportive steps:"])
            for step in care_steps:
                title = step.get("title", "")
                instructions = step.get("instructions", "")
                parts.append(f"• {title}" + (f" — {instructions}" if instructions else ""))
        questions = differential.get("doctor_questions") or []
        if questions:
            parts.extend(["", "Questions to ask your clinician:"])
            parts.extend(f"• {question}" for question in questions[:4])
        warnings = differential.get("red_flag_warnings") or []
        if warnings:
            parts.extend(["", "Seek urgent medical care for:"])
            parts.extend(f"• {warning}" for warning in warnings[:5])
        parts.extend([
            "",
            "This is not a diagnosis. Please consult a licensed clinician, especially if symptoms worsen or you are concerned.",
        ])
        return "\n".join(parts)

    async def __call__(
        self,
        state: DoctorAgentState,
    ) -> dict:

        structured_prompt = state.get(
            "structured_prompt",
            "",
        )

        differential = state.get(
            "differential",
            {},
        )

        # The differential already synthesizes the retrieved sources. Sending
        # those full research results again here exhausted the small Groq TPM
        # allowance, so synthesis consumes only the concise clinical context
        # and the analysis that follows.
        context = compact_text(structured_prompt, 800)
        differential_text = compact_text(json.dumps(differential, ensure_ascii=False, separators=(",", ":")), 1400)
        prompt = f"""
Write a clear, empathetic patient-facing answer based on the clinical analysis below.
The differential already incorporates relevant web and medical-reference evidence.

USER CONTEXT:
{context}

DIFFERENTIAL DIAGNOSIS ANALYSIS:
{differential_text}

Your task:
1. Synthesize the clinical picture clearly for the patient.
2. Outline the primary differential possibilities and explain why the evidence supports them.
3. Highlight safe, non-pharmacological supportive steps.
4. Note any warning signs that require urgent in-person medical evaluation.
5. Emphasize questions the patient should discuss with their physician.

Rules:
- Clearly distinguish evidence from uncertainty.
- Do not prescribe prescription drugs or declare 100% certainty.
- Do not invent facts or fabricate citations.
- Maintain an empathetic and clear tone for patient understanding.
- Recommend appropriate professional medical evaluation where applicable.
"""

        try:
            response = await self.groq.generate_text(
                system_prompt="You are the senior clinical research synthesis expert for DocAgent AI. Be empathetic, evidence-grounded, and careful about uncertainty.",
                user_prompt=prompt,
                temperature=0.2,
            )
            fallback = self.groq.last_provider == "gemini"
            provider = self.groq.last_provider
        except Exception as exc:
            if not self._is_rate_limited(exc):
                raise
            response = self._fallback_response(differential)
            fallback = True
            provider = "local"

        return {
            "final_response": response,
            "synthesis_fallback": fallback,
            "synthesis_provider": provider,
        }
