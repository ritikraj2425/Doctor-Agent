from fastapi import APIRouter,UploadFile, File, Form
from services.input import ProcessInput
router = APIRouter()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    prompt: str = Form(...),
    chat_id: str = Form(...),
    prompt_type: str = Form(...)
):
    response = await ProcessInput().process(file, prompt, chat_id, prompt_type)
    return response

