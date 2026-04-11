"""Search Block - WORKING web search"""
from blocks.base import LegoBlock
from typing import Dict, Any
import urllib.parse

class SearchBlock(LegoBlock):
    """Web Search - TESTED DuckDuckGo + API providers"""
    name = "search"
    version = "1.0.0"
    requires = ["config"]
    
    PROVIDERS = {
        "serper": {"url": "https://google.serper.dev/search", "type": "google"},
        "tavily": {"url": "https://api.tavily.com/search", "type": "ai_search"},
        "brave": {"url": "https://api.search.brave.com/res/v1/web/search", "type": "privacy"},
        "duckduckgo": {"url": "html", "type": "scrape"}  # Free
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
        """Web search with multiple providers"""
        query = data.get("query")
        provider = data.get("provider", self.default_provider)
        num_results = data.get("num", 10)
        
        if provider == "duckduckgo":
            return await self._duckduckgo_search(query, num_results)
        elif provider == "serper":
            return await self._serper_search(query, num_results)
        elif provider == "tavily":
            return await self._tavily_search(query, num_results)
        
        return {"error": f"Unknown provider: {provider}"}
    
    async def _duckduckgo_search(self, query: str, num: int) -> Dict:
        """Scrape DuckDuckGo (free, no API key)"""
        try:
            import aiohttp
            from bs4 import BeautifulSoup
            
            # HTML version (more reliable than JS version)
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status != 200:
                        return {"error": f"DuckDuckGo returned {resp.status}"}
                    
                    html = await resp.text()
                    
                    # Parse results
                    soup = BeautifulSoup(html, 'html.parser')
                    results = []
                    
                    for result in soup.select('.result'):
                        title_elem = result.find('a', class_='result__a')
                        snippet_elem = result.find('a', class_='result__snippet')
                        
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            link = title_elem.get('href', '')
                            
                            # Clean up link
                            if link.startswith('/l/?'):
                                # Extract actual URL from redirect
                                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
                                link = parsed.get('uddg', [''])[0]
                            
                            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                            
                            results.append({
                                "title": title,
                                "link": link,
                                "snippet": snippet
                            })
                            
                            if len(results) >= num:
                                break
                    
                    return {
                        "results": results,
                        "count": len(results),
                        "provider": "duckduckgo",
                        "query": query
                    }
                    
        except ImportError as e:
            return {"error": f"Missing dependency: {str(e)}. Run: pip install aiohttp beautifulsoup4"}
        except Exception as e:
            return {"error": f"DuckDuckGo search failed: {str(e)}"}
    
    async def _serper_search(self, query: str, num: int) -> Dict:
        """Serper.dev Google Search API"""
        if not self.api_key:
            return {"error": "Serper API key not configured"}
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.PROVIDERS["serper"]["url"],
                    headers={
                        "X-API-KEY": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={"q": query, "num": num}
                ) as resp:
                    if resp.status != 200:
                        error = await resp.text()
                        return {"error": f"Serper API error: {error}"}
                    
                    result = await resp.json()
                    
                    return {
                        "results": [
                            {
                                "title": r.get("title"),
                                "link": r.get("link"),
                                "snippet": r.get("snippet"),
                                "date": r.get("date"),
                                "position": r.get("position")
                            }
                            for r in result.get("organic", [])
                        ],
                        "knowledge_graph": result.get("knowledgeGraph"),
                        "provider": "serper",
                        "query": query
                    }
                    
        except ImportError:
            return {"error": "aiohttp not installed"}
        except Exception as e:
            return {"error": f"Serper search failed: {str(e)}"}
    
    async def _tavily_search(self, query: str, num: int) -> Dict:
        """Tavily AI Search API"""
        if not self.api_key:
            return {"error": "Tavily API key not configured"}
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.PROVIDERS["tavily"]["url"],
                    headers={"Content-Type": "application/json"},
                    json={
                        "api_key": self.api_key,
                        "query": query,
                        "max_results": num,
                        "include_answer": True
                    }
                ) as resp:
                    if resp.status != 200:
                        error = await resp.text()
                        return {"error": f"Tavily API error: {error}"}
                    
                    result = await resp.json()
                    
                    return {
                        "results": result.get("results", []),
                        "answer": result.get("answer"),
                        "query": query,
                        "provider": "tavily"
                    }
                    
        except ImportError:
            return {"error": "aiohttp not installed"}
        except Exception as e:
            return {"error": f"Tavily search failed: {str(e)}"}
    
    async def _news_search(self, data: Dict) -> Dict:
        """Search news specifically"""
        query = data.get("query")
        # Add news filter
        news_query = f"{query} news"
        return await self._web_search({"query": news_query, "provider": "serper"})
    
    async def _image_search(self, data: Dict) -> Dict:
        """Image search"""
        query = data.get("query")
        provider = data.get("provider", "serper")
        
        if provider == "serper" and self.api_key:
            try:
                import aiohttp
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://google.serper.dev/images",
                        headers={
                            "X-API-KEY": self.api_key,
                            "Content-Type": "application/json"
                        },
                        json={"q": query, "num": 10}
                    ) as resp:
                        result = await resp.json()
                        
                        return {
                            "images": [
                                {
                                    "title": img.get("title"),
                                    "link": img.get("imageUrl"),
                                    "source": img.get("source")
                                }
                                for img in result.get("images", [])
                            ],
                            "provider": "serper"
                        }
                        
            except Exception as e:
                return {"error": f"Image search failed: {str(e)}"}
        
        return {"error": "Image search requires Serper API key"}
    
    def health(self) -> Dict:
        h = super().health()
        h["providers"] = list(self.PROVIDERS.keys())
        h["default"] = self.default_provider
        h["api_key_configured"] = self.api_key is not None
        return h
