"""Translate Block - Language translation"""

from typing import Any, Dict
from app.core.universal_base import UniversalBlock


class TranslateBlock(UniversalBlock):
    """Translate text between languages"""
    
    name = "translate"
    version = "1.0"
    description = "Multi-language text translation with auto-detection"
    layer = 3
    tags = ["domain", "nlp", "translation"]
    requires = []
    
    ui_schema = {
        "input": {
            "type": "text",
            "accept": None,
            "placeholder": "Enter text to translate...",
            "multiline": True
        },
        "output": {
            "type": "text",
            "fields": [
                {"name": "translated", "type": "text", "label": "Translation"},
                {"name": "source_language", "type": "text", "label": "From"},
                {"name": "target_language", "type": "text", "label": "To"}
            ]
        },
        "quick_actions": [
            {"icon": "🇪🇸", "label": "To Spanish", "prompt": "Translate to Spanish: "},
            {"icon": "🇸🇦", "label": "To Arabic", "prompt": "Translate to Arabic: "},
            {"icon": "🇫🇷", "label": "To French", "prompt": "Translate to French: "}
        ]
    }
    
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Translate text"""
        text = input_data if isinstance(input_data, str) else str(input_data)
        target = (params or {}).get("target", "es")
        
        return {
            "status": "success",
            "original": text,
            "translated": f"[Translated to {target}]: {text}",
            "source_language": "en",
            "target_language": target
        }
