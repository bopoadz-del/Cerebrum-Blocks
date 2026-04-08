"""PDF Block - Extract text and images from PDF files."""

import io
import os
import base64
from typing import Any, Dict, List, Optional
from app.core.block import BaseBlock, BlockConfig


class PDFBlock(BaseBlock):
    """Extract text, images, and metadata from PDF files."""
    
    def __init__(self):
        super().__init__(BlockConfig(
            name="pdf",
            version="1.0",
            description="Extract text, images, and metadata from PDF files",
            supported_inputs=["file", "file_path"],
            supported_outputs=["text", "images", "metadata"]
        ))
        self._pymupdf_available = self._check_pymupdf()
    
    def _check_pymupdf(self) -> bool:
        """Check if PyMuPDF is available."""
        try:
            import fitz
            return True
        except ImportError:
            return False
    
    async def process(self, input_data: Any, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process PDF and extract content."""
        params = params or {}
        extract_text = params.get("extract_text", True)
        extract_images = params.get("extract_images", False)
        extract_metadata = params.get("extract_metadata", True)
        
        file_path = self._get_file_path(input_data)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        result = {
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
        }
        
        if self._pymupdf_available:
            import fitz
            doc = fitz.open(file_path)
            
            if extract_metadata:
                result["metadata"] = {
                    "page_count": len(doc),
                    "title": doc.metadata.get("title", ""),
                    "author": doc.metadata.get("author", ""),
                    "subject": doc.metadata.get("subject", ""),
                    "creator": doc.metadata.get("creator", ""),
                    "producer": doc.metadata.get("producer", ""),
                    "creation_date": doc.metadata.get("creationDate", ""),
                    "modification_date": doc.metadata.get("modDate", ""),
                }
            
            if extract_text:
                full_text = ""
                pages_text = []
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text = page.get_text()
                    pages_text.append({
                        "page_number": page_num + 1,
                        "text": text,
                        "word_count": len(text.split())
                    })
                    full_text += text + "\n"
                
                result["text"] = full_text
                result["pages"] = pages_text
                result["total_word_count"] = len(full_text.split())
            
            if extract_images:
                images = []
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    img_list = page.get_images()
                    for img_index, img in enumerate(img_list, start=1):
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        if pix.n > 4:
                            pix = fitz.Pixmap(fitz.csRGB, pix)
                        img_data = pix.tobytes("png")
                        images.append({
                            "page_number": page_num + 1,
                            "image_index": img_index,
                            "format": "png",
                            "width": pix.width,
                            "height": pix.height,
                            "size_bytes": len(img_data),
                            "base64": base64.b64encode(img_data).decode("utf-8")
                        })
                result["images"] = images
                result["image_count"] = len(images)
            
            doc.close()
        else:
            # Fallback: basic text extraction
            result["text"] = f"[PDF content - PyMuPDF not installed. File: {file_path}]"
            result["pages"] = []
            result["metadata"] = {"page_count": "unknown"}
        
        result["confidence"] = 0.95 if self._pymupdf_available else 0.5
        return result
    
    def _get_file_path(self, input_data: Any) -> str:
        """Extract file path from input data."""
        if isinstance(input_data, dict):
            if "file_path" in input_data:
                return input_data["file_path"]
            if "source_id" in input_data:
                return f"/app/data/{input_data['source_id']}"
        if isinstance(input_data, str):
            return input_data
        raise ValueError("Invalid input: expected file path or dict with file_path/source_id")
