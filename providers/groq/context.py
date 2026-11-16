from pathlib import Path

from pypdf import PdfReader

from providers.groq.client import GroqClient
from schemas.context import ContextResult
from services.diagnosis_service.prompt_context import compact_text


class GroqContextProvider:
    def __init__(self, client: GroqClient | None = None):
        self.client = client or GroqClient()

    async def understand_context(self, file_path: str | None, prompt: str, file_type: str | None) -> ContextResult:
        system_prompt = """You are an input understanding system for a medical consultation assistant.
Combine the user's text, voice transcript, and any attached document into a concise, faithful clinical context.
Preserve symptoms, duration, relevant history, medicines, allergies, and important numbers. Do not invent facts and do not diagnose or answer the underlying medical question.
Set is_medical=false for requests unrelated to health and provide the short refusal in response. Set is_medical=true for health-related requests. Return only the requested structured data."""
        user_prompt = f"User's input and conversation context:\n{prompt}"
        image_path = None
        if file_path:
            mime = file_type or "application/octet-stream"
            if mime == "application/pdf" or Path(file_path).suffix.lower() == ".pdf":
                pages = PdfReader(file_path).pages
                extracted = "\n\n".join(page.extract_text() or "" for page in pages).strip()
                if not extracted:
                    raise ValueError("This PDF has no selectable text. Please upload a text-based PDF or an image of the page.")
                user_prompt += "\n\nDocument text:\n" + extracted[:40_000]
            elif mime.startswith("image/"):
                image_path = file_path
            elif mime.startswith("text/") or Path(file_path).suffix.lower() == ".txt":
                user_prompt += "\n\nDocument text:\n" + Path(file_path).read_text(encoding="utf-8", errors="replace")[:40_000]
            else:
                raise ValueError("Upload a PDF, image, or text document.")

        # Document extraction can be tens of thousands of characters. Keep
        # enough of the beginning and end to retain the user's question and
        # later document details without exceeding Groq's small TPM tier.
        user_prompt = compact_text(user_prompt, 4000)

        return await self.client.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=ContextResult,
            temperature=0.1,
            image_path=image_path,
            image_mime_type=file_type,
        )
