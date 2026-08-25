from pathlib import Path

from google.genai import types

from providers.gemini.client import GeminiClient
from schemas.context import ContextResult



class GeminiClientChatProvider:
    def __init__(self):
        self.gemini_client = GeminiClient()

    async def understand_context(
        self,
        file_path: str | None,
        prompt: str,
        file_type: str | None,
    ) -> ContextResult:

        system_prompt = """
You are an input understanding system.

Your task is to understand all information provided by the user.

The user may provide:
1. A text prompt.
2. A voice transcription.
3. An uploaded document.

Combine all relevant information into one complete and coherent
representation of what the user is communicating.

Rules:
- Preserve important facts, claims, numbers, names, and relationships.
- Do not invent information.
- Do not answer the user's underlying question.
- Do not verify whether claims are true.
- Do not omit relevant context.
- Convert poorly structured voice transcription into coherent context.

If the request is NOT medical:
- set is_medical=false
- set structured_prompt=""
- set response="This system only handles medical-related questions."
- DO NOT answer the user's original question.

"""

        text_input = f"""
{system_prompt}

User's input:
{prompt}
"""

        contents: list[str | types.Part] = [
            text_input
        ]

        if file_path:
            pdf_bytes = Path(file_path).read_bytes()

            pdf_part = types.Part.from_bytes(
                data=pdf_bytes,
                mime_type=file_type or "application/pdf",
            )

            contents.append(pdf_part)

        response = await self.gemini_client.client.aio.models.generate_content(
            model="gemini-3.7-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ContextResult.model_json_schema(),
            ),
        )

        return ContextResult.model_validate_json(
            response.text
        )