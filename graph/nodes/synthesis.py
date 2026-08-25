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

        prompt = f"""
You are the final medical research synthesis system.

Analyze the user's request using BOTH research sources.

USER CONTEXT:
{state["structured_prompt"]}

WEB RESEARCH:
{state.get("web_results", [])}

BOOK RESEARCH:
{state.get("book_results", [])}

Your task:

1. Identify the most likely disease or medical condition discussed.
2. Explain the evidence supporting that interpretation.
3. Summarize relevant information from the medical book.
4. Summarize relevant information from trusted web sources.
5. Provide potential treatment/management information when supported
   by the evidence.
6. Clearly distinguish evidence from uncertainty.
7. Do not invent facts.
8. Do not claim certainty when the evidence is insufficient.
9. Recommend appropriate professional medical evaluation where applicable.

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
            "final_response": response.text or ""
        }