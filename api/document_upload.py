import asyncio
import json
import logging
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse

from graph.graph import create_graph
from graph.dependencies import create_nodes


router = APIRouter()
logger = logging.getLogger(__name__)


def result_payload(result, chat_id):
    if not result.get("is_medical", False):
        return {"chat_id": result.get("chat_id", chat_id), "is_medical": False,
                "response": result.get("response", "This system only handles medical-related consultations.")}
    return {
        "chat_id": result.get("chat_id", chat_id), "is_medical": True,
        "is_emergency": result.get("is_emergency", False),
        "urgency_level": result.get("urgency_level", "routine"),
        "response": result.get("final_response", ""), "triage": result.get("triage", {}),
        "differential": result.get("differential", {}),
        "possible_causes": result.get("possible_causes", []),
        "medication_check": result.get("medication_check", {}),
        "medicines": result.get("medicines", []), "safety_review": result.get("safety_review", {}),
        "structured_response": result.get("final_structured_response", {}),
        "synthesis_fallback": result.get("synthesis_fallback", False),
        "synthesis_provider": result.get("synthesis_provider", "groq"),
        "providers": {key: result[key] for key in (
            "context_provider", "triage_provider", "root_cause_provider", "synthesis_provider", "medication_provider"
        ) if result.get(key)},
        "book_results": result.get("book_results", []), "web_results": result.get("web_results", []),
    }


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
    prompt: str = Form(""),
    chat_id: str = Form(""),
    prompt_type: str = Form("text"),
    audio_file: UploadFile | None = File(None),
):

    if not chat_id:
        import uuid
        chat_id = f"chat_{uuid.uuid4().hex[:8]}"

    result = await doctor_graph.ainvoke(
        {
            "file": file,
            "audio_file": audio_file,
            "prompt": prompt,
            "chat_id": chat_id,
            "prompt_type": prompt_type,
        }
    )

    return result_payload(result, chat_id)


@router.post("/stream")
async def stream_consultation(
    file: UploadFile | None = File(None), prompt: str = Form(""),
    chat_id: str = Form(""), prompt_type: str = Form("text"),
    audio_file: UploadFile | None = File(None),
):
    chat_id = chat_id or f"chat_{uuid4().hex[:10]}"

    async def events():
        yield "event: status\ndata: " + json.dumps({"status": "started", "chat_id": chat_id}) + "\n\n"
        state = {}
        active_node = "starting"

        async def graph_events_with_keepalive(graph_input):
            queue = asyncio.Queue()

            async def produce():
                try:
                    async for graph_event in doctor_graph.astream_events(graph_input, version="v2"):
                        await queue.put(("event", graph_event))
                except Exception as exc:
                    await queue.put(("error", exc))
                finally:
                    await queue.put(("done", None))

            producer = asyncio.create_task(produce())
            try:
                while True:
                    try:
                        kind, value = await asyncio.wait_for(queue.get(), timeout=15)
                    except asyncio.TimeoutError:
                        yield None
                        continue
                    if kind == "done":
                        break
                    if kind == "error":
                        raise value
                    yield value
            finally:
                if not producer.done():
                    producer.cancel()

        try:
            graph_input = {
                "file": file, "audio_file": audio_file, "prompt": prompt,
                "chat_id": chat_id, "prompt_type": prompt_type,
            }
            async for event in graph_events_with_keepalive(graph_input):
                if event is None:
                    # Keep Vercel and intermediary connections alive while a node awaits a provider.
                    yield ": keep-alive\n\n"
                    continue
                node = event.get("metadata", {}).get("langgraph_node")
                kind = event.get("event")
                if not node or event.get("name") != node:
                    continue
                if kind == "on_chain_start":
                    active_node = node
                    yield "event: activity\ndata: " + json.dumps({"node": node, "status": "started"}) + "\n\n"
                elif kind == "on_chain_end":
                    values = event.get("data", {}).get("output", {})
                    if not isinstance(values, dict):
                        values = {}
                    state.update(values)
                    # Stream the phase outputs the UI presents; never expose
                    # temporary file paths or system instructions.
                    if node in ("web_research", "book_research"):
                        safe_values = {k: values[k] for k in ("web_results", "book_results", "web_research_error", "book_research_error") if k in values}
                    elif node == "triage":
                        safe_values = {k: values[k] for k in ("urgency_level", "is_emergency", "triage") if k in values}
                        safe_values["provider_used"] = values.get("triage_provider")
                    elif node == "understand_context":
                        safe_values = {k: values[k] for k in ("is_medical", "structured_prompt", "response") if k in values}
                        safe_values["provider_used"] = values.get("context_provider")
                    elif node == "process_input":
                        safe_values = {"transcription": values.get("transcription", "")}
                    elif node == "emergency_response":
                        safe_values = {k: values[k] for k in ("final_response", "is_emergency", "urgency_level") if k in values}
                    elif node == "root_cause":
                        safe_values = {k: values[k] for k in ("differential", "possible_causes") if k in values}
                        safe_values["provider_used"] = values.get("root_cause_provider")
                    elif node == "synthesis":
                        safe_values = {"draft_response": values.get("final_response", ""),
                                       "synthesis_fallback": values.get("synthesis_fallback", False),
                                       "synthesis_provider": values.get("synthesis_provider", "groq")}
                    elif node == "medication_verifier":
                        safe_values = {k: values[k] for k in ("medication_check", "medicines") if k in values}
                        safe_values["provider_used"] = values.get("medication_provider")
                    elif node == "safety_guard":
                        safe_values = {k: values[k] for k in ("safety_review", "final_structured_response", "final_response") if k in values}
                    else:
                        safe_values = {}
                    yield "event: step\ndata: " + json.dumps({"node": node, "output": safe_values}, default=str) + "\n\n"
            if "is_medical" not in state:
                raise RuntimeError("Agent graph finished without a final state")
            yield "event: result\ndata: " + json.dumps(result_payload(state, chat_id), default=str) + "\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception as exc:
            logger.exception("Agent stream failed")
            status = getattr(exc, "status_code", None)
            if getattr(exc, "public_message", None):
                reason = exc.public_message
            elif status == 401:
                reason = "Groq rejected the API key. Check GROQ_API_KEY in the server environment."
            elif status == 429:
                reason = "Groq rate limit or usage quota reached. Please wait and retry."
            elif status == 413:
                reason = "Groq rejected an oversized prompt (HTTP 413). Retrieved evidence is now shortened before analysis; retry the consultation."
            elif status == 400 and (getattr(exc, "body", None) or {}).get("error", {}).get("code") == "json_validate_failed":
                reason = "Groq could not finish a valid JSON response within the token limit. Please retry."
            elif status == 400:
                reason = "Groq rejected this model request. Check server logs for the provider's error details."
            elif status:
                reason = f"Groq returned HTTP {status}. Check the configured model and request format."
            elif exc.__class__.__name__ in ("APITimeoutError", "TimeoutError"):
                reason = "The model request timed out. Please retry, or check Groq service status."
            elif exc.__class__.__name__ == "APIConnectionError":
                reason = "The server could not connect to Groq. Check network access and retry."
            else:
                reason = "The phase failed while processing its output. See server logs for details."
            yield "event: error\ndata: " + json.dumps({"phase": active_node, "message": f"{active_node.replace('_', ' ').title()} failed: {reason}"}) + "\n\n"

    return StreamingResponse(events(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no",
    })
