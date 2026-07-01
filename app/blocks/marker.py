"""Marker PDF Block - High-quality PDF to Markdown extraction.

This block wraps `marker-pdf` to convert PDF files into clean Markdown,
preserving headings, tables, lists, and math. It is an optional dependency:
if marker-pdf is not installed, the block returns a clear error so callers
can fall back to the generic `pdf` block.
"""

import logging
import os
import tempfile
from typing import Any, Dict, Optional

from app.core.typed_block import TypedBlock, Schema, ContentType

logger = logging.getLogger(__name__)


def _try_marker(pdf_path: str) -> Optional[Dict[str, Any]]:
    """Convert PDF to Markdown using Marker if available.

    Returns a dict with ``text`` and ``pages`` on success, or ``None`` if
    marker-pdf is not installed or fails. This lets callers fall back to
    other parsers when Marker is unavailable.
    """
    try:
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict
        from marker.output import text_from_rendered
    except ImportError as e:
        logger.info("Marker not installed: %s", e)
        return None

    try:
        converter = PdfConverter(artifact_dict=create_model_dict())
        rendered = converter(pdf_path)
        text, _, _ = text_from_rendered(rendered)
        pages = getattr(rendered, "page_count", len(getattr(rendered, "pages", [])))
        return {"text": text or "", "pages": pages or 1}
    except Exception as e:
        logger.warning("Marker conversion failed for %s: %s", pdf_path, e)
        return None


class MarkerBlock(TypedBlock):
    """Extract clean Markdown from PDF files using Marker."""

    name = "marker"
    version = "1.0.0"
    description = "High-quality PDF to Markdown extraction with Marker"
    layer = 3
    tags = ["domain", "documents", "pdf", "markdown", "typed"]
    requires = []

    default_config = {"max_chars": 200000}

    input_schema = Schema(
        content_type=ContentType.FILE,
        required_fields=["file_path"],
        optional_fields=["path", "url"],
        format_hints={"accept": [".pdf"]},
    )

    output_schema = Schema(
        content_type=ContentType.TEXT,
        required_fields=["text"],
        optional_fields=["pages", "filename", "status", "engine"],
        format_hints={"max_chars": 200000},
    )

    ui_schema = {
        "input": {
            "type": "file",
            "accept": [".pdf"],
            "placeholder": "Upload PDF...",
            "multiline": False,
        },
        "output": {
            "type": "json",
            "fields": [
                {"name": "text", "type": "text", "label": "Markdown"},
                {"name": "pages", "type": "number", "label": "Pages"},
            ],
        },
        "quick_actions": [
            {
                "icon": "📄",
                "label": "Extract Markdown",
                "prompt": "Convert this PDF to clean Markdown",
            },
            {
                "icon": "📊",
                "label": "Extract Tables",
                "prompt": "Extract all tables from this PDF as Markdown tables",
            },
        ],
    }

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Extract Markdown from a PDF using Marker."""
        params = params or {}
        max_chars = params.get("max_chars", 200000)

        # Resolve URL input
        url = None
        if isinstance(input_data, dict):
            url = input_data.get("url")
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
                return {
                    "status": "error",
                    "text": "",
                    "pages": 0,
                    "error": f"Download failed: {str(e)}",
                }

        pdf_path = self._get_pdf_path(input_data)
        if not pdf_path:
            return {"status": "error", "text": "", "pages": 0, "error": "No PDF provided"}
        if not os.path.exists(pdf_path):
            return {
                "status": "error",
                "text": "",
                "pages": 0,
                "error": f"File not found: {pdf_path}",
            }

        marker_result = _try_marker(pdf_path)
        if marker_result is None:
            return {
                "status": "error",
                "text": "",
                "pages": 0,
                "error": (
                    "marker-pdf is not installed or failed to load. "
                    "Install it with: pip install marker-pdf>=1.10.0"
                ),
            }

        return {
            "status": "success",
            "text": marker_result["text"][:max_chars],
            "pages": marker_result["pages"],
            "filename": os.path.basename(pdf_path),
            "file_path": pdf_path,
            "engine": "marker",
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
            file_bytes = input_data.get("file") or input_data.get("pdf_bytes") or input_data.get("bytes")
            if isinstance(file_bytes, bytes):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
                    f.write(file_bytes)
                    return f.name
            return input_data.get("file_path") or input_data.get("path") or input_data.get("url")
        return None
