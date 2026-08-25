from providers.groq.client import GroqClient

class GroqClientTranscriptionProvider:
    def __init__(self, groq_client: GroqClient):
        self.groq_client = groq_client
    
    async def transcribe_audio(self, file_path: str) -> str:

        audio_file =open(file_path, "rb")
        response = await self.groq_client.client.audio.transcriptions.create(
            model='whisper-large-v3-turbo',
            file=audio_file,
            response_format='text'
        )
        audio_file.close()
        return response
