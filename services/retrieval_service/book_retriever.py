import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from providers.qdrant.client import QdrantClientProvider
from langchain_qdrant import QdrantVectorStore
from langchain_cohere import CohereEmbeddings


load_dotenv(".env")


class BookRetriever:
    COLLECTION_NAME = 'medical_books'
    def __init__(self):
        # Defer network checks until this node actually runs. This lets the
        # FastAPI process start even while Qdrant is temporarily unavailable.
        self.vector_store = None

    def _get_vector_store(self):
        if self.vector_store is not None:
            return self.vector_store
        qdrant = QdrantClientProvider()

        cohere_api_key = os.getenv("COHERE_API_KEY")

        if not cohere_api_key:
            raise ValueError("COHERE_API_KEY is not set")


        embeddings = CohereEmbeddings(
            model="embed-v4.0",
            cohere_api_key=cohere_api_key,
        )


        self.vector_store = QdrantVectorStore(
            embedding=embeddings,
            collection_name=self.COLLECTION_NAME,
            client=qdrant.client
        )
        return self.vector_store

    async def search(self, query: str, k: int = 5) -> list[dict]:
        documents = await self._get_vector_store().asimilarity_search(query, k=k)
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in documents
        ]
