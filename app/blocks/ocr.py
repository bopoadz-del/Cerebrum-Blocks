"""OCR Block - Extract text from images with preprocessing"""

import os
import io
import tempfile
from typing import Any, Dict
from app.core.universal_base import UniversalBlock


class OCRBlock(UniversalBlock):
    """Optical Character Recognition from images with quality enhancement"""
    
    name = "ocr"
    version = "1.1"
    description = "Extract text from images using OCR with preprocessing"
    layer = 3
    tags = ["domain", "vision", "ocr", "documents"]
    requires = []
    
    default_config = {
        "languages": ["en"],
        "preprocess": True,
        "deskew": False,
        "contrast_factor": 1.5
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
        },
        "quick_actions": [
            {"icon": "🔍", "label": "Extract Text", "prompt": "Extract all text from this image"},
            {"icon": "🔢", "label": "Extract Numbers", "prompt": "Extract all numbers and measurements from this image"},
            {"icon": "📋", "label": "Full OCR", "prompt": "Perform full OCR and return structured content"}
        ]
    }
    
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Extract text from image with preprocessing"""
        params = params or {}
        
        image_path = self._get_image_path(input_data)
        if not image_path:
            return {"status": "error", "text": "", "confidence": 0, "error": "No image provided"}
        
        if not os.path.exists(image_path):
            return {"status": "error", "text": "", "confidence": 0, "error": f"File not found: {image_path}"}
        
        preprocess = params.get("preprocess", self.config.get("preprocess", True))
        languages = params.get("languages", self.config.get("languages", ["en"]))
        
        # Preprocess image if enabled
        if preprocess:
            image_path = self._preprocess_image(image_path)
        
        # Try EasyOCR (pure Python, no system deps)
        try:
            import easyocr
            reader = easyocr.Reader(languages, gpu=False)
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
                "engine": "easyocr",
                "preprocessed": preprocess
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
    
    def _preprocess_image(self, image_path: str) -> str:
        """Enhance image for better OCR quality"""
        from PIL import Image, ImageEnhance, ImageFilter
        
        img = Image.open(image_path)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Resize if too small (improve effective DPI)
        min_dim = min(img.size)
        if min_dim < 1000:
            scale = 1200 / min_dim
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to grayscale
        gray = img.convert('L')
        
        # Enhance contrast
        contrast_factor = self.config.get("contrast_factor", 1.5)
        enhancer = ImageEnhance.Contrast(gray)
        gray = enhancer.enhance(contrast_factor)
        
        # Sharpen
        gray = gray.filter(ImageFilter.SHARPEN)
        
        # Apply mild denoise
        gray = gray.filter(ImageFilter.MedianFilter(size=3))
        
        # Adaptive thresholding: if image is low-contrast, apply point operation
        # to increase separation between text and background
        stat = gray.getextrema()
        if stat and (stat[1] - stat[0]) < 100:
            # Low dynamic range — apply threshold
            gray = gray.point(lambda x: 0 if x < 128 else 255, '1').convert('L')
        
        # Save to temp file
        fd, temp_path = tempfile.mkstemp(suffix="_ocr.png")
        os.close(fd)
        gray.save(temp_path, "PNG")
        return temp_path
