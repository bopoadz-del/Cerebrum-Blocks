"""OCR Block - Extract text from images using EasyOCR"""

import os
from typing import Any, Dict
from app.core.universal_base import UniversalBlock


class OCRBlock(UniversalBlock):
    """Optical Character Recognition from images using EasyOCR (pure Python, no system dependencies)"""
    
    name = "ocr"
    version = "1.0"
    description = "Extract text from images using OCR"
    layer = 3
    tags = ["domain", "vision", "ocr", "documents"]
    requires = []
    
    default_config = {
        "languages": ["en"],
        "confidence_threshold": 0.6
    }
    
    ui_schema = {
        "input": {
            "type": "image",
            "accept": [".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"],
            "placeholder": "Upload image to extract text...",
            "multiline": False
        },
        "output": {
            "type": "text",
            "fields": [
                {"name": "text", "type": "text", "label": "Extracted Text"},
                {"name": "confidence", "type": "percentage", "label": "Confidence"},
                {"name": "word_count", "type": "number", "label": "Words Found"}
            ]
        },
        "quick_actions": [
            {"icon": "👁️", "label": "Extract Text", "prompt": "Extract all text from this image"},
            {"icon": "📄", "label": "Scan Document", "prompt": "Scan this document and extract all text content"}
        ]
    }
    
    def __init__(self, hal_block=None, config: Dict = None):
        super().__init__(hal_block, config)
        self._reader = None
    
    def _get_reader(self):
        """Lazy initialization of EasyOCR reader"""
        if self._reader is None:
            try:
                import easyocr
                languages = self.config.get("languages", ["en"])
                self._reader = easyocr.Reader(languages, gpu=False)
            except Exception as e:
                raise RuntimeError(f"Failed to initialize EasyOCR: {e}")
        return self._reader
    
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Extract text from image using EasyOCR"""
        params = params or {}
        
        # Get image path
        image_path = self._get_image_path(input_data)
        if not image_path:
            return {
                "status": "error",
                "text": "",
                "confidence": 0,
                "error": "No image provided"
            }
        
        # Check if file exists
        if not os.path.exists(image_path):
            return {
                "status": "error", 
                "text": "",
                "confidence": 0,
                "error": f"Image file not found: {image_path}"
            }
        
        try:
            # Use EasyOCR for text extraction
            reader = self._get_reader()
            results = reader.readtext(image_path)
            
            if not results:
                return {
                    "status": "success",
                    "text": "",
                    "confidence": 0,
                    "word_count": 0,
                    "message": "No text detected in image"
                }
            
            # Combine all detected text
            texts = []
            confidences = []
            
            for (bbox, text, conf) in results:
                if text.strip():
                    texts.append(text)
                    confidences.append(conf)
            
            full_text = "\n".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            word_count = len(full_text.split())
            
            return {
                "status": "success",
                "text": full_text,
                "confidence": round(avg_confidence, 2),
                "word_count": word_count,
                "detections": len(results),
                "engine": "easyocr"
            }
            
        except ImportError:
            return {
                "status": "error",
                "text": "",
                "confidence": 0,
                "error": "EasyOCR not installed. Run: pip install easyocr"
            }
        except Exception as e:
            return {
                "status": "error",
                "text": "",
                "confidence": 0,
                "error": f"OCR failed: {str(e)}"
            }
    
    def _get_image_path(self, input_data: Any) -> str:
        """Extract image path from input"""
        if isinstance(input_data, str):
            return input_data
        elif isinstance(input_data, dict):
            return input_data.get("file_path") or input_data.get("url") or input_data.get("path")
        return None
