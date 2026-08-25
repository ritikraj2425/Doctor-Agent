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

        prompt = f"""
You are the final medical research synthesis system.

Analyze the user's request using BOTH independent research sources.

USER CONTEXT:
{structured_prompt}

WEB RESEARCH:
{json.dumps(web_results, ensure_ascii=False, indent=2)}

BOOK RESEARCH:
{json.dumps(book_results, ensure_ascii=False, indent=2)}

Your task:

1. Identify the most likely disease or medical condition discussed.
2. Explain the evidence supporting that interpretation.
3. Summarize the relevant information retrieved from the medical book.
4. Summarize the relevant information retrieved from trusted web sources.
5. Provide treatment or management information only when supported by
   the available evidence.
6. Clearly distinguish evidence from uncertainty.
7. Do not invent facts.
8. Do not claim certainty when the evidence is insufficient.
9. Preserve source provenance whenever possible.
10. Recommend appropriate professional medical evaluation where applicable.

Important:
- The book research and web research are independent evidence sources.
- Do not assume that either source is automatically correct.
- Do not fabricate citations or sources.
- If the evidence is insufficient to identify a condition, explicitly say so.

Return a clear medical research response.
"""

        response = await self.gemini.client.aio.models.generate_content(
            model="gemini-3.7-flash",
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.2,
            ),
        )

        return {
            "final_response": response.text or "",
        }