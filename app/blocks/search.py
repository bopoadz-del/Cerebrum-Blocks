"""Search Block - DuckDuckGo HTML search (no API key) + Serper fallback"""

import os
from typing import Any, Dict
from urllib.parse import quote_plus, urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.universal_base import UniversalBlock

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
_TIMEOUT = 15.0
_DDG_URL = "https://html.duckduckgo.com/html/"
_SERPER_URL = "https://google.serper.dev/search"


async def _search_duckduckgo(query: str, num: int) -> list:
    async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True) as client:
        resp = await client.post(_DDG_URL, data={"q": query, "b": "", "kl": "us-en"})
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    for result in soup.select(".result"):
        # skip ads
        if result.select_one(".badge--ad"):
            continue

        title_el = result.select_one(".result__a")
        snippet_el = result.select_one(".result__snippet")
        url_el = result.select_one(".result__url")

        if not title_el:
            continue

        href = title_el.get("href", "")
        # organic results have direct hrefs; skip any remaining redirects
        if "duckduckgo.com/y.js" in href or "duckduckgo.com/l/" in href:
            continue

        results.append({
            "title": title_el.get_text(strip=True),
            "url": href,
            "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
            "display_url": url_el.get_text(strip=True) if url_el else urlparse(href).netloc,
            "source": "duckduckgo",
        })

        if len(results) >= num:
            break

    return results


async def _search_serper(query: str, num: int, api_key: str) -> list:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            _SERPER_URL,
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": num},
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("organic", [])[:num]:
        results.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "display_url": urlparse(item.get("link", "")).netloc,
            "position": item.get("position"),
            "source": "serper",
        })
    return results


class SearchBlock(UniversalBlock):
    """Real-time web search — DuckDuckGo HTML (no API key) or Serper API"""

    name = "search"
    version = "2.0"
    description = "Search the web via DuckDuckGo (no key required) or Serper API"
    layer = 3
    tags = ["domain", "search", "web"]
    requires = []

    ui_schema = {
        "input": {
            "type": "text",
            "accept": None,
            "placeholder": "Search the web...",
            "multiline": False,
        },
        "output": {
            "type": "list",
            "fields": [{"name": "results", "type": "array", "label": "Results"}],
        },
        "quick_actions": [{"icon": "🔍", "label": "Search", "prompt": "Search for"}],
    }

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        params = params or {}
        query = (
            input_data
            if isinstance(input_data, str)
            else params.get("query", "")
        )
        if isinstance(input_data, dict):
            query = input_data.get("query", input_data.get("text", ""))

        num = min(int(params.get("num_results", 10)), 20)

        if not query or not query.strip():
            return {"status": "error", "error": "Query is required"}

        serper_key = os.getenv("SERPER_API_KEY", "")
        provider = "serper" if serper_key else "duckduckgo"

        try:
            if serper_key:
                results = await _search_serper(query.strip(), num, serper_key)
            else:
                results = await _search_duckduckgo(query.strip(), num)

            return {
                "status": "success",
                "query": query,
                "results": results,
                "total": len(results),
                "provider": provider,
            }

        except httpx.TimeoutException:
            return {"status": "error", "error": "Search timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e), "provider": provider}
