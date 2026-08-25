import os
from langchain_tavily import TavilySearch
from dotenv import load_dotenv
load_dotenv('.env')

class TavilyWebSearchProvider:

    TRUSTED_DOMAINS = [
        "who.int",
        "cdc.gov",
        "nih.gov",
        "ncbi.nlm.nih.gov",
        "pubmed.ncbi.nlm.nih.gov",
        "medlineplus.gov",
        "nhs.uk",
        "mayoclinic.org",
    ]
    def __init__(self):
        api_key = os.getenv('TAVILY_API_KEY')
        if not api_key:
            raise ValueError("TAVILY_API_KEY is not set")
        self.tavily_search = TavilySearch(
            max_results=5,
            topic="general",
            search_depth="advanced",
            include_raw_content=True,
            api_key=api_key
        )

    async def search(self, query: str) -> list[dict]:
        return await self.tavily_search.ainvoke(
            {
                "query": query,
                "include_domains": self.TRUSTED_DOMAINS,
            }
        )