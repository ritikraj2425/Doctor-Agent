import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv('.env')

class QdrantClientProvider:

    def __init__(self):
        url = os.getenv('QDRANT_URL')
        api_key = os.getenv('QDRANT_API_KEY')

        if not url:
            raise ValueError("QDRANT_URL is not set")
        if not api_key:
            raise ValueError("QDRANT_API_KEY is not set")

        self.client = QdrantClient(
            url=url,
            api_key=api_key,
            timeout=300,
        )