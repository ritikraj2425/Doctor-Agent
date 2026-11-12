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

    # Triage
    triage: dict
    is_emergency: bool
    urgency_level: str

    # Research branches
    web_results: list[dict]
    book_results: list[dict]

    # Clinical Analysis
    differential: dict
    possible_causes: list[dict]

    # Medication Verification
    medication_check: dict
    medicines: list[dict]

    # Safety & Final Output
    safety_review: dict
    final_structured_response: dict
    final_response: str
