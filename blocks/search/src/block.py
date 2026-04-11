from blocks.base import LegoBlock
from typing import Dict, Any

class SearchBlock(LegoBlock):
    """Web Search - Multiple providers"""
    name = "search"
    version = "1.0.0"
    requires = ["config"]
    
    PROVIDERS = {
        "serper": {"url": "https://google.serper.dev/search", "type": "google"},
        "tavily": {"url": "https://api.tavily.com/search", "type": "ai_search"},
        "brave": {"url": "https://api.search.brave.com/res/v1/web/search", "type": "privacy"},
        "duckduckgo": {"url": "html", "type": "scrape"}
    }
    
    def __init__(self, hal_block, config: Dict[str, Any]):
        super().__init__(hal_block, config)
        self.api_key = config.get("serper_key") or config.get("tavily_key")
        self.default_provider = config.get("default", "duckduckgo")
        
    async def execute(self, input_data: Dict) -> Dict:
        action = input_data.get("action")
        if action == "search":
            return await self._web_search(input_data)
        elif action == "news":
            return await self._news_search(input_data)
        elif action == "images":
            return await self._image_search(input_data)
        return {"error": "Unknown action"}
    
    async def _web_search(self, data: Dict) -> Dict:
        query = data.get("query")
        provider = data.get("provider", self.default_provider)
        num_results = data.get("num", 10)
        
        if provider == "duckduckgo":
            import aiohttp
            from bs4 import BeautifulSoup
            
            search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url) as resp:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    results = [
                        {
                            "title": r.find('a').get_text() if r.find('a') else "",
                            "link": r.find('a')['href'] if r.find('a') else "",
                            "snippet": r.find('a', class_='result__snippet').get_text() if r.find('a', class_='result__snippet') else ""
                        }
                        for r in soup.select('.result')
                    ]
                    
                    return {"results": results[:num_results], "provider": "duckduckgo"}
        
        elif provider == "serper" and self.api_key:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.PROVIDERS["serper"]["url"],
                    headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
                    json={"q": query, "num": num_results}
                ) as resp:
                    result = await resp.json()
                    return {
                        "results": [
                            {
                                "title": r.get("title"),
                                "link": r.get("link"),
                                "snippet": r.get("snippet"),
                                "date": r.get("date")
                            }
                            for r in result.get("organic", [])
                        ],
                        "provider": "serper"
                    }
        
        return {"results": [], "provider": provider, "error": "Provider not configured"}
    
    async def _news_search(self, data: Dict) -> Dict:
        return await self._web_search(data)
    
    async def _image_search(self, data: Dict) -> Dict:
        return {"results": [], "provider": "pending"}
    
    def health(self) -> Dict:
        h = super().health()
        h["providers"] = list(self.PROVIDERS.keys())
        h["default"] = self.default_provider
        return h
