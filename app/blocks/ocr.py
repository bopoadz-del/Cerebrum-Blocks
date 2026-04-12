"""OCR Block - Extract text from images"""

import os
from typing import Any, Dict
from app.core.universal_base import UniversalBlock


class OCRBlock(UniversalBlock):
    """Optical Character Recognition from images"""
    
    name = "ocr"
    version = "1.0"
    description = "Extract text from images using OCR"
    layer = 3
    tags = ["domain", "vision", "ocr", "documents"]
    requires = []
    
    default_config = {
        "languages": ["en"]
    }
    
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
        }
    }
    
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Extract text from image"""
        params = params or {}
        
        # Get image path
        image_path = self._get_image_path(input_data)
        if not image_path:
            return {"status": "error", "text": "", "confidence": 0, "error": "No image provided"}
        
        if not os.path.exists(image_path):
            return {"status": "error", "text": "", "confidence": 0, "error": f"File not found: {image_path}"}
        
        # Try EasyOCR (pure Python, no system deps)
        try:
            import easyocr
            reader = easyocr.Reader(["en"], gpu=False)
            results = reader.readtext(image_path)
            
            if not results:
                return {"status": "success", "text": "", "confidence": 0, "message": "No text detected"}
            
            texts = [r[1] for r in results if r[1].strip()]
            confs = [r[2] for r in results]
            
            full_text = "\n".join(texts)
            avg_conf = sum(confs) / len(confs) if confs else 0
            
            return {
                "status": "success",
                "text": full_text,
                "confidence": round(avg_conf, 2),
                "word_count": len(full_text.split()),
                "engine": "easyocr"
            }
            
        except ImportError:
            return {"status": "error", "text": "", "confidence": 0, "error": "EasyOCR not installed"}
        except Exception as e:
            return {"status": "error", "text": "", "confidence": 0, "error": f"OCR failed: {str(e)}"}
    
    def _get_image_path(self, input_data: Any) -> str:
        """Extract image path from input"""
        if isinstance(input_data, str):
            return input_data
        elif isinstance(input_data, dict):
            return input_data.get("file_path") or input_data.get("path") or input_data.get("url")
        return None
