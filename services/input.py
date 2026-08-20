from typing import Any

from fastapi import UploadFile

from services.audio_service.speech_to_text import SpeechToTextProcessor
from services.document_service.image_process import ImageProcessor
from services.document_service.pdf_process import PDFProcessor


class ProcessInput:

    def __init__(
        self,
        pdf_processor: PDFProcessor | None = None,
        image_processor: ImageProcessor | None = None,
        speech_processor: SpeechToTextProcessor | None = None,
    ) -> None:
        self._pdf_processor = pdf_processor or PDFProcessor()
        self._image_processor = image_processor or ImageProcessor()
        self._speech_processor = speech_processor or SpeechToTextProcessor()

    async def process(self,
        file: UploadFile | None,
        prompt: str,
        chat_id: str,
        prompt_type: str
    ) -> dict[str, Any]:
        response = {
            "document": self._process_document(file),
            "chat_id": chat_id,
        }

        if prompt_type == "audio" and file is not None:
            response["text"] = self._speech_processor.process_audio(file.filename)
        else:
            response["prompt"] = prompt

        return response

    def _process_document(self, file: UploadFile | None) -> dict[str, str]:
        if file is None or not file.content_type:
            return {"message": "Unsupported file type"}
        
        if file.content_type == "application/pdf":
            return self._pdf_processor.process_pdf(file.filename)

        if file.content_type.startswith("image/"):
            return self._image_processor.process_image(file.filename)

        return {"message": "Unsupported file type"}
        




