"""Search Block - Web search"""

from typing import Any, Dict
from app.core.universal_base import UniversalBlock


class SearchBlock(UniversalBlock):
    """Web search capabilities"""
    
    name = "search"
    version = "1.0"
    layer = 3
    tags = ["domain", "search", "web"]
    requires = []
    
    ui_schema = {
        "input": {
            "type": "text",
            "accept": None,
            "placeholder": "Search the web...",
            "multiline": False
        },
        "output": {
            "type": "list",
            "fields": [
                {"name": "results", "type": "array", "label": "Results"}
            ]
        },
        "quick_actions": [
            {"icon": "🔍", "label": "Search", "prompt": "Search for"}
        ]
    }
    
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Search the web"""
        query = input_data if isinstance(input_data, str) else ""
        
        return {
            "status": "success",
            "query": query,
            "results": [
                {"title": "Result 1", "url": "https://example.com/1", "snippet": "..."},
                {"title": "Result 2", "url": "https://example.com/2", "snippet": "..."}
            ]
        }
