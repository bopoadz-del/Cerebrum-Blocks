"""OCR Block - Extract text from images using Tesseract"""

import os
from typing import Any, Dict
from app.core.universal_base import UniversalBlock


class OCRBlock(UniversalBlock):
    """Optical Character Recognition from images using Tesseract"""
    
    name = "ocr"
    version = "1.0"
    description = "Extract text from images using OCR"
    layer = 3
    tags = ["domain", "vision", "ocr", "documents"]
    requires = []
    
    default_config = {
        "language": "eng",
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
    
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Extract text from image using OCR"""
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
        
        # Try EasyOCR first (no system dependencies)
        easyocr_result = await self._try_easyocr(image_path, params)
        if easyocr_result.get("status") == "success":
            return easyocr_result
        
        # Fallback: Try Tesseract OCR
        try:
            import pytesseract
            from PIL import Image
            
            # Open image
            image = Image.open(image_path)
            
            # Configure OCR
            lang = params.get("language", self.config.get("language", "eng"))
            
            # Extract text
            text = pytesseract.image_to_string(image, lang=lang)
            
            # Get confidence data
            data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
            
            # Calculate average confidence
            confidences = [int(c) for c in data["conf"] if int(c) > 0]
            avg_confidence = sum(confidences) / len(confidences) / 100 if confidences else 0.5
            
            # Count words
            word_count = len(text.split())
            
            return {
                "status": "success",
                "text": text.strip(),
                "confidence": round(avg_confidence, 2),
                "word_count": word_count,
                "language": lang,
                "image_size": f"{image.width}x{image.height}"
            }
            
        except ImportError:
            return {
                "status": "error",
                "text": "",
                "confidence": 0,
                "error": "No OCR engine available. Install easyocr or pytesseract."
            }
        except Exception as e:
            return {
                "status": "error",
                "text": "",
                "confidence": 0,
                "error": f"OCR failed: {str(e)}"
            }
    
    async def _try_easyocr(self, image_path: str, params: Dict) -> Dict:
        """Fallback OCR using EasyOCR"""
        try:
            import easyocr
            
            reader = easyocr.Reader(['en'])
            results = reader.readtext(image_path)
            
            # Combine text
            texts = [result[1] for result in results]
            full_text = "\n".join(texts)
            
            # Average confidence
            confidences = [result[2] for result in results]
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.5
            
            return {
                "status": "success",
                "text": full_text,
                "confidence": round(avg_conf, 2),
                "word_count": len(full_text.split()),
                "engine": "easyocr"
            }
            
        except ImportError:
            return {
                "status": "error",
                "text": "",
                "confidence": 0,
                "error": "No OCR engine available. Install pytesseract or easyocr."
            }
    
    def _get_image_path(self, input_data: Any) -> str:
        """Extract image path from input"""
        if isinstance(input_data, str):
            return input_data
        elif isinstance(input_data, dict):
            return input_data.get("file_path") or input_data.get("url") or input_data.get("path")
        return None
