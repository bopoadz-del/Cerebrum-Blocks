"""PDF Block - Extract text, tables, images from PDF files"""

import os
from typing import Any, Dict, List, Optional
from app.core.universal_base import UniversalBlock


class PDFBlock(UniversalBlock):
    """Extract text, tables, images, and metadata from PDF files."""
    
    name = "pdf"
    version = "1.1"
    description = "Extract text, tables, images from PDF files"
    layer = 3  # Domain
    tags = ["domain", "documents", "pdf"]
    requires = []
    
    default_config = {
        "extract_tables": True,
        "extract_images": False,
        "ocr_fallback": True
    }
    
    # UI Schema - Universal UI Shell configuration
    ui_schema = {
        "input": {
            "type": "file",
            "accept": [".pdf"],
            "placeholder": "Drop PDF or click to upload...",
            "multiline": False
        },
        "output": {
            "type": "json",
            "fields": [
                {"name": "text", "type": "text", "label": "Extracted Text"},
                {"name": "pages", "type": "number", "label": "Pages"},
                {"name": "tables", "type": "array", "label": "Tables Found"}
            ]
        },
        "quick_actions": [
            {"icon": "📄", "label": "Extract Text", "prompt": "Extract all text from this PDF"},
            {"icon": "📊", "label": "Find Tables", "prompt": "Extract tables from this PDF"}
        ]
    }
    
    def __init__(self, hal_block=None, config: Dict = None):
        super().__init__(hal_block, config)
        self._pymupdf_available = self._check_pymupdf()
    
    def _check_pymupdf(self) -> bool:
        try:
            import fitz
            return True
        except ImportError:
            return False
    
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Extract content from PDF"""
        params = params or {}
        
        # Get PDF source
        if isinstance(input_data, str):
            if input_data.startswith("http"):
                pdf_path = await self._download_pdf(input_data)
            else:
                pdf_path = input_data
        elif isinstance(input_data, dict):
            pdf_path = input_data.get("file_path") or input_data.get("url")
        else:
            return {"error": "Invalid input: expected file path or URL"}
        
        if not pdf_path or not os.path.exists(pdf_path):
            return {"error": f"PDF file not found: {pdf_path}"}
        
        # Extract using PyMuPDF if available
        if self._pymupdf_available:
            return await self._extract_with_pymupdf(pdf_path, params)
        else:
            # Fallback: return basic info
            return {
                "text": f"[PDF placeholder - PyMuPDF not installed] {pdf_path}",
                "pages": 0,
                "tables": [],
                "images": []
            }
    
    async def _download_pdf(self, url: str) -> str:
        """Download PDF from URL"""
        import httpx
        import tempfile
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            
        temp_path = tempfile.mktemp(suffix=".pdf")
        with open(temp_path, "wb") as f:
            f.write(resp.content)
        return temp_path
    
    async def _extract_with_pymupdf(self, pdf_path: str, params: Dict) -> Dict:
        """Extract using PyMuPDF"""
        import fitz
        
        doc = fitz.open(pdf_path)
        
        text = ""
        tables = []
        images = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text += page.get_text()
            
            # Extract tables if enabled
            if params.get("extract_tables", self.config.get("extract_tables")):
                # Basic table detection via text blocks
                blocks = page.get_text("blocks")
                if len(blocks) > 4:  # Potential table
                    tables.append({
                        "page": page_num + 1,
                        "blocks": len(blocks)
                    })
        
        doc.close()
        
        return {
            "text": text[:10000],  # Limit text length
            "pages": len(doc),
            "tables": tables,
            "images": images,
            "metadata": {
                "filename": os.path.basename(pdf_path),
                "size_bytes": os.path.getsize(pdf_path)
            }
        }
