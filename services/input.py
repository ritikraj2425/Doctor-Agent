from typing import Any

from fastapi import UploadFile

from services.audio_service.speech_to_text import SpeechToTextProcessor
from services.document_service.pdf_process import PDFProcessor
from services.file_service import FileService

class ProcessInput:

    def __init__(
        self,
        pdf_processor: PDFProcessor | None = None,
        speech_processor: SpeechToTextProcessor | None = None,
    ) -> None:
        self._pdf_processor = pdf_processor or PDFProcessor()
        self._speech_processor = speech_processor or SpeechToTextProcessor()

    async def process(self,
        file: UploadFile | None,
        prompt: str,
        chat_id: str,
        prompt_type: str,
        audio_file: UploadFile | None = None
    ) -> dict[str, Any]:

        response: dict[str, Any]= {
            "prompt": prompt,
            "chat_id": chat_id,
            "file_path": None,
            "file_type": None,
        }

        audio_path = None
        file_path = None
        try:
            audio_path = await FileService().save_file(audio_file) if audio_file and prompt_type == "audio" else None
            file_path = await FileService().save_file(file) if file else None
            response["file_path"] = file_path
            response["file_type"] = file.content_type if file else None

            if prompt_type == "audio" and audio_file is not None:
                transcript = await self._speech_processor.process_audio(audio_path)
                response["transcription"] = transcript
                response["prompt"] = f"{prompt}\n\nLatest voice message: {transcript}" if prompt else transcript
        except Exception:
            if file_path:
                await FileService().delete_file(file_path)
            raise
        finally:
            if audio_path:
                await FileService().delete_file(audio_path)
        return response
