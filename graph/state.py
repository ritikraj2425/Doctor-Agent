from typing import TypedDict

from fastapi import UploadFile


class DoctorAgentState(TypedDict, total=False):
    file: UploadFile | None
    audio_file: UploadFile | None

    prompt: str
    chat_id: str
    prompt_type: str

    file_path: str | None
    file_type: str | None

    is_medical: bool
    structured_prompt: str
    response: str | None

    # Research branches
    web_results: list[dict]
    book_results: list[dict]

    # Final
    final_response: str