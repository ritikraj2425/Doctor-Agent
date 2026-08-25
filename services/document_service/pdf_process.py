from langchain_community.document_loaders import PyPDFLoader

class PDFProcessor:

    async def process_pdf(self, file_path: str) -> dict[str, str]:

        loader = PyPDFLoader(file_path)
        pages = loader.load_and_split()
        text = " ".join([page.page_content for page in pages])
        return {"message": "PDF processed successfully", "text": text}

        
