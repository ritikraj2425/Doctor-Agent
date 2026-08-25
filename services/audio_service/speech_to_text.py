from providers.groq.transcription import GroqClientTranscriptionProvider
from providers.groq.client import GroqClient

class SpeechToTextProcessor:
    def __init__(self):
        self.transcription_provider = GroqClientTranscriptionProvider(GroqClient())

    async def process_audio(self, file_path: str):
        return await self.transcription_provider.transcribe_audio(file_path)
