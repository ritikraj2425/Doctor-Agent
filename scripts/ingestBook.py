from pathlib import Path

from services.retrieval_service.document_ingestion import BookIngestionService


def main():

    ingestion_service = BookIngestionService()

    books_dir = Path("books")

    pdf_files = list(books_dir.glob("*.pdf"))

    if not pdf_files:
        raise RuntimeError("No PDF files found in books/")

    for pdf in pdf_files:

        print(f"Ingesting: {pdf}")

        chunk_count = ingestion_service.ingest_pdf(
            str(pdf)
        )

        print(
            f"Finished {pdf.name}: "
            f"{chunk_count} chunks"
        )


if __name__ == "__main__":
    main()