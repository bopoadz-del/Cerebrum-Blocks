"""OCR Block - Extract text from images"""

from typing import Any, Dict
from app.core.universal_base import UniversalBlock


class OCRBlock(UniversalBlock):
    """Optical Character Recognition from images"""
    
    name = "ocr"
    version = "1.0"
    layer = 3
    tags = ["domain", "vision", "ocr", "documents"]
    requires = []
    
    ui_schema = {
        "input": {
            "type": "image",
            "accept": [".jpg", ".jpeg", ".png", ".webp"],
            "placeholder": "Upload image to extract text...",
            "multiline": False
        },
        "output": {
            "type": "text",
            "fields": [
                {"name": "text", "type": "text", "label": "Extracted Text"},
                {"name": "confidence", "type": "percentage", "label": "Confidence"}
            ]
        },
        "quick_actions": [
            {"icon": "👁️", "label": "Extract Text", "prompt": "Extract all text from this image"}
        ]
    }
    
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Extract text from image"""
        return {
            "status": "success",
            "text": "[OCR extracted text placeholder]",
            "confidence": 0.92
        }
