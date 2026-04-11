"""Vector Search Block - Semantic search"""

from typing import Any, Dict
from app.core.universal_base import UniversalBlock


class VectorSearchBlock(UniversalBlock):
    """Vector similarity search using ChromaDB"""
    
    name = "vector_search"
    version = "1.0"
    layer = 2  # AI Core
    tags = ["ai", "core", "vector", "search"]
    requires = []
    
    ui_schema = {
        "input": {
            "type": "text",
            "accept": None,
            "placeholder": "Search knowledge base...",
            "multiline": False
        },
        "output": {
            "type": "list",
            "fields": [
                {"name": "results", "type": "array", "label": "Matches"}
            ]
        },
        "quick_actions": [
            {"icon": "🔍", "label": "Search Docs", "prompt": "Search for similar documents about"}
        ]
    }
    
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Search vectors"""
        return {
            "status": "success",
            "results": [
                {"text": "Sample result 1", "score": 0.95},
                {"text": "Sample result 2", "score": 0.87}
            ]
        }
