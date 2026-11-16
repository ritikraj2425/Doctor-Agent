import asyncio
import logging

from providers.groq.client import GroqClient

logger = logging.getLogger(__name__)

class GroqClientTranscriptionProvider:
    def __init__(self, groq_client: GroqClient):
        self.groq_client = groq_client
    
    async def transcribe_audio(self, file_path: str) -> str:

        try:
            with open(file_path, "rb") as audio_file:
                response = await asyncio.wait_for(
                    self.groq_client.client.audio.transcriptions.create(
                        model='whisper-large-v3-turbo',
                        file=audio_file,
                        response_format='text'
                    ), timeout=90,
                )
            self.groq_client.last_provider = "groq"
            return response
        except Exception as groq_error:
            if not self.groq_client._is_rate_limited(groq_error):
                raise
            try:
                from providers.gemini.client import GeminiClient
                logger.info("Groq transcription rate limit reached; retrying transcription with Gemini")
                transcript = await GeminiClient().transcribe_audio(file_path)
            except Exception as gemini_error:
                logger.warning("Groq transcription rate limit reached and Gemini fallback failed", exc_info=gemini_error)
                raise self.groq_client._fallback_error(gemini_error) from gemini_error
            self.groq_client.last_provider = "gemini"
            return transcript
