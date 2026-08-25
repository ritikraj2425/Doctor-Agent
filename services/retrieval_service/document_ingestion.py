import os
from pathlib import Path
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from langchain_cohere import CohereEmbeddings

from providers.qdrant.client import QdrantClientProvider


load_dotenv(".env")


class BookIngestionService:

    COLLECTION_NAME = "medical_books"

    def __init__(self):
        self.qdrant = QdrantClientProvider()

        cohere_api_key = os.getenv("COHERE_API_KEY")

        if not cohere_api_key:
            raise ValueError("COHERE_API_KEY is not set")

        self.embeddings = CohereEmbeddings(
            model="embed-v4.0",
            cohere_api_key=cohere_api_key,
        )

    def ingest_pdf(
        self,
        file_path: str,
    ) -> int:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        loader = PyPDFLoader(str(path))
        pages = loader.load()

        if not pages:
            raise ValueError(
                f"No pages extracted from PDF: {file_path}"
            )

        non_empty_pages = [
            page
            for page in pages
            if page.page_content.strip()
        ]

        print("Total pages:", len(pages))
        print(
            "Pages containing text:",
            len(non_empty_pages)
        )

        if not non_empty_pages:
            raise ValueError(
                f"No text extracted from PDF: {file_path}"
            )

        print("First page text:")
        print(non_empty_pages[0].page_content[:500])

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            add_start_index=True,
        )

        chunks = splitter.split_documents(
            non_empty_pages
        )

        for chunk in chunks:
            chunk.metadata["source_file"] = path.name

        print("Total chunks:", len(chunks))

        if not chunks:
            raise ValueError(
                f"No chunks created from PDF: {file_path}"
            )

        url = os.environ["QDRANT_URL"]
        api_key = os.environ["QDRANT_API_KEY"]

        # Connect to the collection that already exists.
        vector_store = QdrantVectorStore.from_existing_collection(
            collection_name=self.COLLECTION_NAME,
            embedding=self.embeddings,
            url=url,
            api_key=api_key,
        )

        batch_size = 16
        start_index = 15392

        for start in range(
            start_index,
            len(chunks),
            batch_size,
        ):
            end = min(
                start + batch_size,
                len(chunks),
            )

            batch = chunks[start:end]

            print(
                f"Uploading chunks {start + 1}-{end} "
                f"of {len(chunks)}"
            )

            total_chars = sum(
                len(doc.page_content)
                for doc in batch
            )

            vector_store.add_documents(batch)

            estimated_tokens = total_chars / 4

            if estimated_tokens > 60_000:
                time.sleep(60)
            else:
                time.sleep(10)

        return len(chunks)