import os
from fastapi import UploadFile

class FileService:
    async def save_file(self, file: UploadFile) -> str:
        os.makedirs("temp", exist_ok=True)

        file_path = f"temp/{file.filename}"

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        return file_path
    async def delete_file(self, file_path: str):
        import os
        if os.path.exists(file_path):
            os.remove(file_path)

        
