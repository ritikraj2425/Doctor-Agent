from services.input import ProcessInput
from services.context_service.context_provider import ContextProvider
from services.triage_service.triage_provider import TriageProvider
from services.retrieval_service.book_retriever import BookRetriever
from providers.web.search import TavilyWebSearchProvider
from services.diagnosis_service.root_cause_provider import RootCauseProvider
from services.medication_service.medication_verifier import MedicationVerifier
from services.safety_service.safety_guard import SafetyGuard

from graph.nodes.process_input import ProcessInputNode
from graph.nodes.understand_context import UnderstandContextNode
from graph.nodes.triage import TriageNode
from graph.nodes.emergency import EmergencyResponseNode
from graph.nodes.web_research import WebResearchNode
from graph.nodes.book_research import BookResearchNode
from graph.nodes.root_cause import RootCauseNode
from graph.nodes.synthesis import SynthesisNode
from graph.nodes.medication_verifier import MedicationVerifierNode
from graph.nodes.safety_guard import SafetyGuardNode


def create_nodes():

    # Services & Providers
    process_input = ProcessInput()
    context_provider = ContextProvider()
    triage_provider = TriageProvider()
    book_retriever = BookRetriever()
    web_search_provider = TavilyWebSearchProvider()
    root_cause_provider = RootCauseProvider()
    medication_verifier = MedicationVerifier()
    safety_guard = SafetyGuard()

    # Graph Nodes
    process_input_node = ProcessInputNode(
        process_input=process_input
    )

    understand_context_node = UnderstandContextNode(
        context_provider=context_provider
    )

    triage_node = TriageNode(
        triage_provider=triage_provider
    )

    emergency_response_node = EmergencyResponseNode()

    book_research_node = BookResearchNode(
        retriever=book_retriever
    )

    web_research_node = WebResearchNode(
        search_provider=web_search_provider
    )

    root_cause_node = RootCauseNode(
        root_cause_provider=root_cause_provider
    )

    synthesis_node = SynthesisNode()

    medication_verifier_node = MedicationVerifierNode(
        medication_verifier=medication_verifier
    )

    safety_guard_node = SafetyGuardNode(
        safety_guard=safety_guard
    )

    return (
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
    )
