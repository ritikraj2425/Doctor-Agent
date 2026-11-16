from providers.groq.context import GroqContextProvider
from services.file_service import FileService
from schemas.context import ContextResult


class ContextProvider:
    def __init__(self, groq_provider: GroqContextProvider | None = None):
        self.groq_provider = groq_provider or GroqContextProvider()

    async def process(self, file_path: str | None, prompt: str, file_type: str | None) -> ContextResult:
        try:
            return await self.groq_provider.understand_context(
                file_path=file_path,
                prompt=prompt,
                file_type=file_type,
            )
        finally:
            if file_path:
                await FileService().delete_file(file_path)
