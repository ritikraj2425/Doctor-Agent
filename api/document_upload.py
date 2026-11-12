from fastapi import APIRouter, UploadFile, File, Form

from graph.graph import create_graph
from graph.dependencies import create_nodes


router = APIRouter()


(
    process_input_node,
    understand_context_node,
    triage_node,
    emergency_response_node,
    book_research_node,
    web_research_node,
    root_cause_node,
    synthesis_node,
    medication_verifier_node,
    safety_guard_node,
) = create_nodes()


doctor_graph = create_graph(
    process_input_node=process_input_node,
    understand_context_node=understand_context_node,
    triage_node=triage_node,
    emergency_response_node=emergency_response_node,
    book_research_node=book_research_node,
    web_research_node=web_research_node,
    root_cause_node=root_cause_node,
    synthesis_node=synthesis_node,
    medication_verifier_node=medication_verifier_node,
    safety_guard_node=safety_guard_node,
)


@router.post("/upload")
async def upload_document(
    file: UploadFile | None = File(None),
    prompt: str = Form(...),
    chat_id: str = Form(...),
    prompt_type: str = Form(...),
    audio_file: UploadFile | None = File(None),
):

    result = await doctor_graph.ainvoke(
        {
            "file": file,
            "audio_file": audio_file,
            "prompt": prompt,
            "chat_id": chat_id,
            "prompt_type": prompt_type,
        }
    )

    # 1. Non-medical rejection
    if not result.get("is_medical", False):
        return {
            "chat_id": result.get("chat_id", chat_id),
            "is_medical": False,
            "response": result.get(
                "response",
                "This system only handles medical-related consultations.",
            ),
        }

    # 2. Full clinical consultation response
    return {
        "chat_id": result.get("chat_id", chat_id),
        "is_medical": True,
        "is_emergency": result.get("is_emergency", False),
        "urgency_level": result.get("urgency_level", "routine"),
        "response": result.get("final_response", ""),
        "triage": result.get("triage", {}),
        "differential": result.get("differential", {}),
        "possible_causes": result.get("possible_causes", []),
        "medication_check": result.get("medication_check", {}),
        "medicines": result.get("medicines", []),
        "safety_review": result.get("safety_review", {}),
        "structured_response": result.get("final_structured_response", {}),
        "book_results": result.get("book_results", []),
        "web_results": result.get("web_results", []),
    }
