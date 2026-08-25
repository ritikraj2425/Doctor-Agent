from services.input import ProcessInput
from services.context_service.context_provider import ContextProvider
from services.retrieval_service.book_retriever import BookRetriever
from providers.web.search import TavilyWebSearchProvider


from graph.nodes.process_input import ProcessInputNode
from graph.nodes.understand_context import UnderstandContextNode
from graph.nodes.web_research import WebResearchNode
from graph.nodes.book_research import BookResearchNode
from graph.nodes.synthesis import SynthesisNode


def create_nodes():

    process_input = ProcessInput()
    context_provider = ContextProvider()
    book_retriever = BookRetriever()
    web_search_provider = TavilyWebSearchProvider()




    process_input_node = ProcessInputNode(
        process_input=process_input
    )

    understand_context_node = UnderstandContextNode(
        context_provider=context_provider
    )

    book_research_node = BookResearchNode(
        retriever=book_retriever
    )

    web_research_node = WebResearchNode(
        search_provider=web_search_provider
    )

    synthesis_node = SynthesisNode()


    return (
        process_input_node,
        understand_context_node,
        book_research_node,
        web_research_node,
        synthesis_node
    )