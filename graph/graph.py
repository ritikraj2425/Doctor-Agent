from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from graph.state import DoctorAgentState
from graph.nodes.process_input import ProcessInputNode
from graph.nodes.understand_context import UnderstandContextNode
from graph.nodes.book_research import BookResearchNode
from graph.nodes.web_research import WebResearchNode
from graph.nodes.synthesis import SynthesisNode


def route_after_context(state: DoctorAgentState):

    is_medical = state.get("is_medical", False)

    if is_medical is False:
        return END

    return [
        Send("web_research", state),
        Send("book_research", state),
    ]


def create_graph(
    process_input_node: ProcessInputNode,
    understand_context_node: UnderstandContextNode,
    book_research_node: BookResearchNode,
    web_research_node: WebResearchNode,
    synthesis_node: SynthesisNode,
):

    builder = StateGraph(DoctorAgentState)

    builder.add_node(
        "process_input",
        process_input_node,
    )

    builder.add_node(
        "understand_context",
        understand_context_node,
    )

    builder.add_node(
        "book_research",
        book_research_node,
    )

    builder.add_node(
        "web_research",
        web_research_node,
    )

    builder.add_node(
        "synthesis",
        synthesis_node,
    )

    builder.add_edge(
        START,
        "process_input",
    )

    builder.add_edge(
        "process_input",
        "understand_context",
    )

    builder.add_conditional_edges(
        "understand_context",
        route_after_context,
    )

    builder.add_edge(
        "web_research",
        "synthesis",
    )

    builder.add_edge(
        "book_research",
        "synthesis",
    )

    builder.add_edge(
        "synthesis",
        END,
    )

    return builder.compile()