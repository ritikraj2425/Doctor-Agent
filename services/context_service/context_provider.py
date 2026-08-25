from providers.gemini.chat import GeminiClientChatProvider
from services.file_service import FileService
from schemas.context import ContextResult

class ContextProvider:

    def __init__(self):
        self.gemini_client = GeminiClientChatProvider()

    async def process(
        self,
        file_path: str | None,
        prompt: str,
        file_type: str | None,
    ) -> ContextResult:

        try:
            context = await self.gemini_client.understand_context(
                file_path=file_path,
                prompt=prompt,
                file_type=file_type,
            )

            return context

        finally:
            if file_path:
                await FileService().delete_file(file_path)