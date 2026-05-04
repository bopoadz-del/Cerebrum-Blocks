"""OCR Block v2 - Extract text from images using TypedBlock

This is the v2 implementation using the TypedBlock system with schema validation.
Uses pytesseract for real OCR.
"""

import os
import io
import tempfile
from typing import Any, Dict

from app.core.typed_block import TypedBlock
from app.core.schema_registry import TextContent


class OCRBlockV2(TypedBlock):
    """Optical Character Recognition from images - v2 with schema support"""
    
    name = "ocr_v2"
    version = "2.0"
    description = "Extract text from images using OCR with typed output"
    layer = 3
    tags = ["domain", "vision", "ocr", "documents", "v2"]
    requires = []
    
    default_config = {
        "languages": ["en"],
        "preprocess": True,
        "deskew": False,
        "contrast_factor": 1.5
    }
    
    # Input: image path or dict with image info
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string"},
            "path": {"type": "string"},
            "url": {"type": "string"},
            "image_path": {"type": "string"}
        },
        "anyOf": [
            {"required": ["file_path"]},
            {"required": ["path"]},
            {"required": ["url"]},
            {"required": ["image_path"]}
        ]
    }
    
    # Output: TextContent schema
    output_schema = TextContent
    
    # Type declarations for orchestrator
    accepted_input_types = ["ImageContent", "FileContent"]
    produced_output_types = ["TextContent"]
    
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
        """Extract text from image and return TextContent format using pytesseract."""
        params = params or {}
        
        # Download from URL if needed (handles bare URL strings and InputAdapter wrapping)
        url = None
        if isinstance(input_data, str) and input_data.startswith("http"):
            url = input_data
        elif isinstance(input_data, dict):
            url = input_data.get("url")
            if not url:
                raw = input_data.get("text") or input_data.get("input") or ""
                if raw.startswith("http"):
                    url = raw
        if not url and isinstance(params, dict):
            url = params.get("url")

        if url:
            import httpx
            try:
                async with httpx.AsyncClient(follow_redirects=True) as client:
                    response = await client.get(url, timeout=30)
                    response.raise_for_status()
                    ext = ".jpg"
                    for candidate in [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"]:
                        if candidate in url.lower():
                            ext = candidate
                            break
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
                        f.write(response.content)
                        input_data = f.name
            except Exception as e:
                return self._error_response(f"Download failed: {str(e)}")

        image_path = self._get_image_path(input_data)
        if not image_path:
            return self._error_response("No image provided")

        if not os.path.exists(image_path):
            return self._error_response(f"File not found: {image_path}")
        
        preprocess = params.get("preprocess", self.config.get("preprocess", True))
        languages = params.get("languages", self.config.get("languages", ["en"]))
        
        # Detect if input is a PDF and convert pages to images
        page_images = self._prepare_images(image_path, preprocess)
        if not page_images:
            return self._error_response("Could not process input file")
        
        # Real OCR using pytesseract only
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            return self._error_response(
                "pytesseract not installed. Run: pip install pytesseract pillow"
            )

        all_texts = []
        all_confs = []

        try:
            for page_img_path in page_images:
                img = Image.open(page_img_path)
                text = pytesseract.image_to_string(img)
                if text.strip():
                    all_texts.append(text.strip())
                    # pytesseract.image_to_string does not return confidence;
                    # use image_to_data for per-word confidence when available
                    try:
                        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                        conf_values = [int(c) for c in data["conf"] if int(c) > 0]
                        if conf_values:
                            all_confs.append(sum(conf_values) / len(conf_values) / 100.0)
                        else:
                            all_confs.append(0.0)
                    except Exception:
                        all_confs.append(0.0)
        except Exception as e:
            return self._error_response(f"Tesseract OCR failed: {str(e)}")

        if not all_texts:
            return {
                "text": "",
                "source": "ocr",
                "confidence": 0,
                "metadata": {
                    "message": "No text detected",
                    "word_count": 0,
                    "engine": "pytesseract",
                    "preprocessed": preprocess,
                    "extracted_at": self._timestamp()
                }
            }
        
        full_text = "\n".join(all_texts)
        avg_conf = sum(all_confs) / len(all_confs) if all_confs else 0
        
        # Return TextContent format
        return {
            "text": full_text,
            "source": "ocr",
            "confidence": round(avg_conf, 2),
            "metadata": {
                "word_count": len(full_text.split()),
                "engine": "pytesseract",
                "preprocessed": preprocess,
                "pages": len(page_images),
                "extracted_at": self._timestamp()
            }
        }
    
    def _get_image_path(self, input_data: Any) -> str:
        """Extract image path from input, writing bytes to a temp file if needed."""
        if isinstance(input_data, bytes):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
                f.write(input_data)
                return f.name
        if isinstance(input_data, str):
            return input_data
        if isinstance(input_data, dict):
            file_bytes = input_data.get("file") or input_data.get("image_bytes") or input_data.get("bytes")
            if isinstance(file_bytes, bytes):
                ext = ".png"
                for candidate in [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"]:
                    if candidate in str(input_data.get("filename", "")).lower():
                        ext = candidate
                        break
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
                    f.write(file_bytes)
                    return f.name
            return (
                input_data.get("file_path")
                or input_data.get("path")
                or input_data.get("url")
                or input_data.get("image_path")
            )
        return None
    
    def _prepare_images(self, file_path: str, preprocess: bool = True) -> list:
        """Convert input to a list of image file paths (handles PDFs and images)."""
        from PIL import Image
        
        is_pdf = file_path.lower().endswith(".pdf")
        if not is_pdf:
            # Try to open as image; if it fails, try as PDF via PyMuPDF
            try:
                Image.open(file_path)
                # It's a valid image
                if preprocess:
                    return [self._preprocess_image(file_path)]
                return [file_path]
            except Exception:
                is_pdf = True
        
        if is_pdf:
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                images = []
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(dpi=200)
                    img_path = tempfile.mktemp(suffix=f"_page{page_num + 1}.png")
                    pix.save(img_path)
                    if preprocess:
                        img_path = self._preprocess_image(img_path)
                    images.append(img_path)
                doc.close()
                return images
            except ImportError:
                return []
            except Exception:
                return []
        
        return []
    
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
        stat = gray.getextrema()
        if stat and (stat[1] - stat[0]) < 100:
            # Low dynamic range — apply threshold
            gray = gray.point(lambda x: 0 if x < 128 else 255, '1').convert('L')
        
        # Save to temp file
        fd, temp_path = tempfile.mkstemp(suffix="_ocr.png")
        os.close(fd)
        gray.save(temp_path, "PNG")
        return temp_path
    
    def _error_response(self, message: str) -> Dict:
        """Return standardized error response"""
        return {
            "text": "",
            "source": "ocr",
            "confidence": 0,
            "metadata": {
                "error": message,
                "extracted_at": self._timestamp()
            }
        }
    
    def _timestamp(self) -> str:
        """Get current ISO timestamp"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
