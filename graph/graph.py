from langgraph.graph import StateGraph, START, END

from graph.state import DoctorAgentState
from graph.nodes.process_input import ProcessInputNode
from graph.nodes.understand_context import UnderstandContextNode
from graph.nodes.triage import TriageNode
from graph.nodes.emergency import EmergencyResponseNode
from graph.nodes.book_research import BookResearchNode
from graph.nodes.web_research import WebResearchNode
from graph.nodes.root_cause import RootCauseNode
from graph.nodes.synthesis import SynthesisNode
from graph.nodes.medication_verifier import MedicationVerifierNode
from graph.nodes.safety_guard import SafetyGuardNode


def route_after_context(state: DoctorAgentState):
    """Non-medical queries exit; medical queries proceed to triage."""
    is_medical = state.get("is_medical", False)
    if not is_medical:
        return END
    return "triage"


def route_after_triage(state: DoctorAgentState):
    """Emergencies fast-path to emergency node; routine/urgent fork into parallel research."""
    is_emergency = state.get("is_emergency", False)
    if is_emergency:
        return "emergency_response"

    # Parallel research: both web and book run concurrently
    return ["web_research", "book_research"]


def create_graph(
    process_input_node: ProcessInputNode,
    understand_context_node: UnderstandContextNode,
    triage_node: TriageNode,
    emergency_response_node: EmergencyResponseNode,
    book_research_node: BookResearchNode,
    web_research_node: WebResearchNode,
    root_cause_node: RootCauseNode,
    synthesis_node: SynthesisNode,
    medication_verifier_node: MedicationVerifierNode,
    safety_guard_node: SafetyGuardNode,
):

    builder = StateGraph(DoctorAgentState)

    # === Add all nodes ===
    builder.add_node("process_input", process_input_node)
    builder.add_node("understand_context", understand_context_node)
    builder.add_node("triage", triage_node)
    builder.add_node("emergency_response", emergency_response_node)
    builder.add_node("book_research", book_research_node)
    builder.add_node("web_research", web_research_node)
    builder.add_node("root_cause", root_cause_node)
    builder.add_node("synthesis", synthesis_node)
    builder.add_node("medication_verifier", medication_verifier_node)
    builder.add_node("safety_guard", safety_guard_node)

    # === Sequential: input processing & context extraction ===
    builder.add_edge(START, "process_input")
    builder.add_edge("process_input", "understand_context")

    # === Conditional: medical check ===
    builder.add_conditional_edges(
        "understand_context",
        route_after_context,
        {END: END, "triage": "triage"},
    )

    # === Conditional: triage routing ===
    builder.add_conditional_edges(
        "triage",
        route_after_triage,
        ["emergency_response", "web_research", "book_research"],
    )

    # === Emergency fast-path ===
    builder.add_edge("emergency_response", "safety_guard")

    # === Parallel research converges at root_cause ===
    builder.add_edge("web_research", "root_cause")
    builder.add_edge("book_research", "root_cause")

    # === Post-research clinical pipeline ===
    builder.add_edge("root_cause", "synthesis")
    builder.add_edge("synthesis", "medication_verifier")
    builder.add_edge("medication_verifier", "safety_guard")

    # === Safety guardrail to END ===
    builder.add_edge("safety_guard", END)

    return builder.compile()
