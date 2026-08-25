import os
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv(".env")

class GroqClient:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")
        self.client = AsyncGroq(api_key=api_key)

