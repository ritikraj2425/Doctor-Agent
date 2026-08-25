from fastapi import APIRouter, UploadFile, File, Form

from graph.graph import create_graph
from graph.dependencies import create_nodes


router = APIRouter()


(
    process_input_node,
    understand_context_node,
    book_research_node,
    web_research_node,
    synthesis_node,
) = create_nodes()


doctor_graph = create_graph(
    process_input_node,
    understand_context_node,
    book_research_node,
    web_research_node,
    synthesis_node,
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

    if not result.get("is_medical", False):
        return {
            "chat_id": result["chat_id"],
            "response": result["response"],
        }

    return {
        "chat_id": result["chat_id"],
        "response": result["final_response"],
        "book_results": result.get("book_results", []),
        "web_results": result.get("web_results", []),
    }
