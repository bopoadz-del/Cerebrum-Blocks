"""PDF Block - Extract text from PDF files with Typed Schema"""

import os
import tempfile
from typing import Any, Dict
from app.core.typed_block import TypedBlock, Schema, ContentType


class PDFBlock(TypedBlock):
    """Extract text from PDF files with typed output"""
    
    name = "pdf"
    version = "2.0.0"
    description = "Extract text from PDF files"
    layer = 3
    tags = ["domain", "documents", "pdf", "typed"]
    requires = []
    
    default_config = {
        "extract_tables": True
    }
    
    # Type schemas for chain validation
    input_schema = Schema(
        content_type=ContentType.FILE,
        required_fields=["file_path"],
        optional_fields=["path", "url"],
        format_hints={"accept": [".pdf"]}
    )
    
    output_schema = Schema(
        content_type=ContentType.PDF,
        required_fields=["text"],
        optional_fields=["pages", "filename", "status"],
        format_hints={"max_chars": 20000}
    )
    
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
        },
        "quick_actions": [
            {"icon": "📄", "label": "Extract Text", "prompt": "Extract all text from this PDF"},
            {"icon": "📊", "label": "Extract Tables", "prompt": "Extract all tables from this PDF as structured data"},
            {"icon": "📝", "label": "Summarize", "prompt": "Summarize the key points of this document"}
        ]
    }
    
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Extract text from PDF"""
        params = params or {}
        
        # If input is a URL, download it first
        url = None
        if isinstance(input_data, dict):
            url = input_data.get("url")
            # InputAdapter wraps bare strings as {"text": "..."} — check for URL there
            if not url:
                raw = input_data.get("text") or input_data.get("input") or ""
                if raw.startswith("http"):
                    url = raw
        elif isinstance(input_data, str) and input_data.startswith("http"):
            url = input_data
        
        if url:
            import httpx
            try:
                async with httpx.AsyncClient(follow_redirects=True) as client:
                    response = await client.get(url, timeout=30)
                    response.raise_for_status()
                    suffix = ".pdf" if ".pdf" in url.lower() else ".tmp"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                        f.write(response.content)
                        input_data = f.name
            except Exception as e:
                return {"status": "error", "text": "", "pages": 0, "error": f"Download failed: {str(e)}"}
        
        # Get PDF path (handles bytes, strings, dicts)
        pdf_path = self._get_pdf_path(input_data)
        if not pdf_path:
            return {"status": "error", "text": "", "pages": 0, "error": "No PDF provided"}

        if not os.path.exists(pdf_path):
            return {"status": "error", "text": "", "pages": 0, "error": f"File not found: {pdf_path}"}

        ext = os.path.splitext(pdf_path)[1].lower()

        # Handle Excel spreadsheets (XLS/XLSX)
        if ext in ('.xls', '.xlsx'):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(pdf_path, read_only=True, data_only=True)
                parts = []
                for sheet_name in wb.sheetnames:
                    ws = wb[sheet_name]
                    parts.append(f"=== Sheet: {sheet_name} ===")
                    for row in ws.iter_rows(values_only=True):
                        row_text = '\t'.join(str(c) if c is not None else '' for c in row)
                        if row_text.strip():
                            parts.append(row_text)
                wb.close()
                text = '\n'.join(parts)
                return {
                    "status": "success",
                    "text": text[:200000],
                    "pages": len(wb.sheetnames) if hasattr(wb, 'sheetnames') else 1,
                    "filename": os.path.basename(pdf_path),
                    "file_path": pdf_path,
                    "engine": "openpyxl",
                }
            except Exception as e:
                return {"status": "error", "text": "", "pages": 0, "error": f"Excel read failed: {str(e)}"}

        # Handle Word documents (DOCX)
        if ext in ('.doc', '.docx'):
            try:
                import docx as python_docx
                doc = python_docx.Document(pdf_path)
                text = '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
                return {
                    "status": "success",
                    "text": text[:200000],
                    "pages": 1,
                    "filename": os.path.basename(pdf_path),
                    "file_path": pdf_path,
                    "engine": "python-docx",
                }
            except ImportError:
                pass  # Fall through — python-docx not installed
            except Exception as e:
                return {"status": "error", "text": "", "pages": 0, "error": f"Word read failed: {str(e)}"}

        # Try real PDF libraries in order: pdfplumber, PyPDF2, PyMuPDF
        last_error = None
        
        # 1. Try pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    text += page_text + "\n"
                pages = len(pdf.pages)
                return {
                    "status": "success",
                    "text": text[:200000],
                    "pages": pages,
                    "filename": os.path.basename(pdf_path),
                    "file_path": pdf_path,
                    "engine": "pdfplumber",
                }
        except ImportError:
            last_error = "pdfplumber not installed"
        except Exception as e:
            last_error = f"pdfplumber failed: {str(e)}"
        
        # 2. Try PyPDF2
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
            pages = len(reader.pages)
            return {
                "status": "success",
                "text": text[:200000],
                "pages": pages,
                "filename": os.path.basename(pdf_path),
                "file_path": pdf_path,
                "engine": "PyPDF2",
            }
        except ImportError:
            last_error = "PyPDF2 not installed"
        except Exception as e:
            last_error = f"PyPDF2 failed: {str(e)}"
        
        # 3. Try PyMuPDF fallback
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
                "text": text[:200000],
                "pages": pages,
                "filename": os.path.basename(pdf_path),
                "file_path": pdf_path,
                "engine": "pymupdf",
            }
        except ImportError:
            last_error = "PyMuPDF not installed"
        except Exception as e:
            last_error = f"PyMuPDF failed: {str(e)}"
        
        return {
            "status": "error",
            "text": "",
            "pages": 0,
            "error": f"No PDF parser available. {last_error}. Install one of: pdfplumber, PyPDF2, or PyMuPDF",
        }
    
    def _get_pdf_path(self, input_data: Any) -> str:
        """Extract PDF path from input, writing bytes to a temp file if needed."""
        if isinstance(input_data, bytes):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
                f.write(input_data)
                return f.name
        if isinstance(input_data, str):
            return input_data
        if isinstance(input_data, dict):
            # Check for explicit file bytes inside dict
            file_bytes = input_data.get("file") or input_data.get("pdf_bytes") or input_data.get("bytes")
            if isinstance(file_bytes, bytes):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
                    f.write(file_bytes)
                    return f.name
            return input_data.get("file_path") or input_data.get("path") or input_data.get("url")
        return None
