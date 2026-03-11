# app/services/live_researcher.py
import asyncio
from tavily import TavilyClient
from app.config import settings
from app.services.llm_factory import get_ollama_llm


class SasiLiveResearcher:
    def __init__(self):
        # We use a lower temperature for facts to prevent hallucination
        self.llm = get_ollama_llm(model_name="llama3.1:8b", temperature=0.1, max_tokens=2048)
        self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)

    async def execute(self, query: str):
        # IMPROVEMENT: Simplify the query for the search engine
        # "Generate a table of SASI placements" -> "SASI Institute placement statistics recruiters 2024"
        search_query = query.lower().replace("generate a table of", "").replace("what are the", "").replace("tell me about", "").strip()
        print(f"🔍 [Pro Search] Optimized Query: {search_query}")

        try:
            # 1. Targeted search and content extraction
            search_result = await asyncio.to_thread(
                self.client.search,
                query=f"site:sasi.ac.in {search_query}",
                search_depth="advanced",
                max_results=5,
                include_raw_content=False,
                include_answer=False
            )

            # 2. Extract context from results
            context_parts = []
            for result in search_result.get("results", []):
                context_parts.append(
                    f"SOURCE URL: {result['url']}\nCONTENT: {result['content']}"
                )

            full_context = "\n---\n".join(context_parts)

            if not full_context:
                return {
                    "answer": "I found no live data for this on the SASI website.",
                    "sources": []
                }

            # 3. AI synthesis
            SYSTEM_PROMPT = """You are FusedChat Studio, a high-intelligence Research AI for SASI Institute.
            You are currently reading the LIVE college website.

            YOUR GOAL: Answer the question accurately using the provided context.

            STYLE RULES:
            1. Use **bold** for names, designations, and key dates.
            2. If you find a schedule or data list, format it as a Markdown Table.
            3. Use emojis to make the response lively (e.g., 🎓, 🚌, 📄).
            4. At the end, clearly list the 'Verified Source Links' used.
            """

            USER_PROMPT = f"USER QUESTION: {query}\n\nLIVE DATA FOUND:\n{full_context}"

            print("🧠 [AI] Synthesizing live web data...")
            response = await self.llm.ainvoke([
                ("system", SYSTEM_PROMPT),
                ("human", USER_PROMPT)
            ])

            return {
                "answer": response.content,
                "sources": [r["url"] for r in search_result.get("results", [])]
            }

        except Exception as e:
            print(f"❌ Search Error: {e}")
            return {"answer": f"Search failed: {str(e)}", "sources": []}


if __name__ == "__main__":
    async def run():
        researcher = SasiLiveResearcher()
        res = await researcher.execute("Who is the HOD of CSE?")
        print(res["answer"])

    asyncio.run(run())