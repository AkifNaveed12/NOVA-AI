"""
MODULE 4 — Live Search Engine
======================================
Provides live information retrieval via Tavily search API,
with a robust fallback to DuckDuckGo (via duckduckgo-search) when keys are missing or quota is exceeded.
Features a 5-minute memory cache to prevent duplicate queries and minimize latency.
"""

from tavily import TavilyClient
from duckduckgo_search import DDGS
import os
import time

class SearchEngine:
    def __init__(self):
        # Explicitly reload/load env just in case
        from dotenv import load_dotenv
        load_dotenv(override=True)
        key = os.getenv("TAVILY_API_KEY", "")
        self.tavily = TavilyClient(api_key=key) if key else None
        self._cache = {}
        self._cache_ttl = 300  # 5-minute cache

    def search(self, query: str, max_results: int = 5) -> dict:
        cache_key = f"{query}:{max_results}"
        if cache_key in self._cache:
            result, ts = self._cache[cache_key]
            if time.time() - ts < self._cache_ttl:
                print(f"[Search] Cache hit for: '{query}'")
                return result

        try:
            # Recheck for key dynamically if tavily wasn't initialized initially
            if not self.tavily:
                key = os.getenv("TAVILY_API_KEY", "")
                if key:
                    self.tavily = TavilyClient(api_key=key)

            if self.tavily:
                print(f"[Search] querying Tavily: '{query}'")
                res = self._tavily_search(query, max_results)
                self._cache[cache_key] = (res, time.time())
                return res
            else:
                print(f"[Search] Tavily key missing. Querying DDG: '{query}'")
                res = self._ddg_search(query, max_results)
                self._cache[cache_key] = (res, time.time())
                return res
        except Exception as e:
            print(f"[Search] Primary failed: {e}. Trying DDG...")
            try:
                res = self._ddg_search(query, max_results)
                self._cache[cache_key] = (res, time.time())
                return res
            except Exception as e_ddg:
                print(f"[Search] DDG fallback failed: {e_ddg}")
                return {"answer": "", "sources": [], "provider": "failed"}

    def _tavily_search(self, query: str, n: int) -> dict:
        resp = self.tavily.search(query=query, max_results=n,
                                   search_depth="basic", include_answer=True)
        return {
            "answer": resp.get("answer", ""),
            "sources": [{"title": r["title"], "url": r["url"],
                         "snippet": r["content"][:200]}
                        for r in resp.get("results", [])],
            "provider": "tavily"
        }

    def _ddg_search(self, query: str, n: int) -> dict:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=n))
        return {
            "answer": results[0]["body"] if results else "",
            "sources": [{"title": r["title"], "url": r["href"],
                         "snippet": r["body"][:200]}
                        for r in results],
            "provider": "duckduckgo"
        }

    def format_for_groq(self, search_result: dict, query: str) -> str:
        """Format search results for injection into Groq context."""
        if not search_result.get("sources"):
            return ""
        lines = [f"Search results for '{query}':"]
        if search_result.get("answer"):
            lines.append(f"Summary: {search_result['answer']}")
        for i, s in enumerate(search_result["sources"][:3], 1):
            lines.append(f"{i}. {s['title']}: {s['snippet']}")
        return "\n".join(lines)

search_engine = SearchEngine()
