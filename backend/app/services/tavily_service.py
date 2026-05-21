from tavily import TavilyClient
from app.core.config import settings

client = TavilyClient(api_key=settings.TAVILY_API_KEY)


class TavilyService:

    @staticmethod
    def search(query: str):

        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=5
        )

        return response