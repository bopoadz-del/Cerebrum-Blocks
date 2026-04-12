"""PDF Block - Extract text from PDF files"""

import os
from typing import Any, Dict
from app.core.universal_base import UniversalBlock


class PDFBlock(UniversalBlock):
    """Extract text from PDF files"""
    
    name = "pdf"
    version = "1.2"
    description = "Extract text from PDF files"
    layer = 3
    tags = ["domain", "documents", "pdf"]
    requires = []
    
    default_config = {
        "extract_tables": True
    }
    
    ui_schema = {
        "input": {
            "type": "file",
            "accept": [".pdf"],
            "placeholder": "Upload PDF...",
            "multiline": False
        },
        "output": {
            "type": "json",
            "fields": [
                {"name": "text", "type": "text", "label": "Text"},
                {"name": "pages", "type": "number", "label": "Pages"}
            ]
        }
    }
    
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Extract text from PDF"""
        params = params or {}
        
        # Get PDF path
        pdf_path = self._get_pdf_path(input_data)
        if not pdf_path:
            return {"status": "error", "text": "", "pages": 0, "error": "No PDF provided"}
        
        if not os.path.exists(pdf_path):
            return {"status": "error", "text": "", "pages": 0, "error": f"File not found: {pdf_path}"}
        
        # Extract using PyMuPDF
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            text = ""
            
            for page in doc:
                text += page.get_text()
            
            pages = len(doc)
            doc.close()
            
            return {
                "status": "success",
                "text": text[:20000],  # Limit output
                "pages": pages,
                "filename": os.path.basename(pdf_path)
            }
            
        except ImportError:
            return {"status": "error", "text": "", "pages": 0, "error": "PyMuPDF not installed"}
        except Exception as e:
            return {"status": "error", "text": "", "pages": 0, "error": f"PDF extraction failed: {str(e)}"}
    
    def _get_pdf_path(self, input_data: Any) -> str:
        """Extract PDF path from input"""
        if isinstance(input_data, str):
            return input_data
        elif isinstance(input_data, dict):
            return input_data.get("file_path") or input_data.get("path") or input_data.get("url")
        return None
