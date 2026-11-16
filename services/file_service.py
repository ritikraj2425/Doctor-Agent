import os
import tempfile
from pathlib import Path
from fastapi import UploadFile

class FileService:
    async def save_file(self, file: UploadFile) -> str:
        # Use a unique temporary path: concurrent uploads must not overwrite
        # one another, and a client supplied filename must never become a path.
        suffix = Path(file.filename or "").suffix.lower()
        if len(suffix) > 12 or not suffix[1:].isalnum():
            suffix = ""
        descriptor, file_path = tempfile.mkstemp(prefix="clarity-", suffix=suffix)
        try:
            with os.fdopen(descriptor, "wb") as output:
                while chunk := await file.read(1024 * 1024):
                    output.write(chunk)
            return file_path
        except Exception:
            try:
                os.close(descriptor)
            except OSError:
                pass
            if os.path.exists(file_path):
                os.remove(file_path)
            raise
    async def delete_file(self, file_path: str):
        import os
        if os.path.exists(file_path):
            os.remove(file_path)

        
