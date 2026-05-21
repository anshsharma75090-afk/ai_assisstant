from app.services.tavily_service import TavilyService
from app.services.gemini_service import GeminiService


class WebAgent:

    @staticmethod
    def handle(user_message: str, conversation_context: str = ""):

        web_results = TavilyService.search(user_message)

        results = web_results.get("results", [])

        context = ""

        for item in results:
            context += f"""
Title: {item.get('title')}

Content:
{item.get('content')}

Source:
{item.get('url')}

-------------------
"""

        wants_sources = any(word in user_message.lower() for word in [
            "source",
            "sources",
            "link",
            "links",
            "reference",
            "references"
        ])

        prompt = f"""
You are a web research AI assistant.

Answer the user using the provided web search results.

Rules:
- Give concise and useful answers
- Use the search context
- Do NOT hallucinate
- Only give source links if the user explicitly asks for them

User Question:
{user_message}

Previous Conversation in this chat:
{conversation_context or "No previous conversation in this chat."}

Search Results:
{context}
"""

        answer = GeminiService.generate_response(prompt)

        if wants_sources:

            sources = "\n\nSources:\n"

            for item in results:
                sources += f"- {item.get('url')}\n"

            answer += sources

        return answer
