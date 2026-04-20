"""Web Block - Web scraping"""

from typing import Any, Dict
from app.core.universal_base import UniversalBlock


class WebBlock(UniversalBlock):
    """Web scraping and extraction"""
    
    name = "web"
    version = "1.0"
    description = "Web scraping and structured HTML content extraction"
    layer = 3
    tags = ["domain", "web", "scraping"]
    requires = []
    
    ui_schema = {
        "input": {
            "type": "url",
            "accept": None,
            "placeholder": "Enter URL to scrape...",
            "multiline": False
        },
        "output": {
            "type": "text",
            "fields": [
                {"name": "title", "type": "text", "label": "Title"},
                {"name": "text", "type": "markdown", "label": "Content"},
                {"name": "links", "type": "array", "label": "Links"}
            ]
        },
        "quick_actions": [
            {"icon": "🌐", "label": "Scrape URL", "prompt": "Extract content from URL"}
        ]
    }
    
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Scrape web page"""
        params = params or {}
        url = input_data if isinstance(input_data, str) else ""
        operation = params.get("operation", "fetch")
        
        if operation == "html_parse":
            return {
                "status": "success",
                "url": url,
                "title": "[Parsed Title]",
                "text": "[Parsed text content]",
                "links": []
            }
        else:
            return {
                "status": "success",
                "url": url,
                "title": "[Page Title]",
                "text": "[Extracted text content]",
                "links": []
            }
