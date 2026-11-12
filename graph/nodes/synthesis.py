import json

from google.genai import types

from graph.state import DoctorAgentState
from providers.gemini.client import GeminiClient


class SynthesisNode:

    def __init__(self):
        self.gemini = GeminiClient()

    async def __call__(
        self,
        state: DoctorAgentState,
    ) -> dict:

        structured_prompt = state.get(
            "structured_prompt",
            "",
        )

        web_results = state.get(
            "web_results",
            [],
        )

        book_results = state.get(
            "book_results",
            [],
        )

        differential = state.get(
            "differential",
            {},
        )

        prompt = f"""
You are the senior clinical research synthesis expert for DocAgent AI.

Provide a comprehensive, empathetic, and evidence-grounded clinical explanation
for the patient based on all available analysis.

USER CONTEXT:
{structured_prompt}

DIFFERENTIAL DIAGNOSIS ANALYSIS:
{json.dumps(differential, ensure_ascii=False, indent=2)}

WEB RESEARCH:
{json.dumps(web_results, ensure_ascii=False, indent=2)}

BOOK RESEARCH:
{json.dumps(book_results, ensure_ascii=False, indent=2)}

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

        response = await self.gemini.generate_content(
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.2,
            ),
        )

        return {
            "final_response": response.text or "",
        }
