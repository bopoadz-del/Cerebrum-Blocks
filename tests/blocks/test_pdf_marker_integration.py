"""Tests for the optional Marker integration inside the PDF block."""

import os
import tempfile

import pytest

from app.blocks import PDFBlock


@pytest.fixture
def pdf_block():
    return PDFBlock()


@pytest.mark.asyncio
async def test_pdf_block_uses_marker_when_requested(pdf_block, monkeypatch):
    """When use_marker=true, the PDF block should prefer Marker results."""

    def _fake_marker(path):
        return {"text": "# Markdown from Marker", "pages": 3}

    monkeypatch.setattr("app.blocks.pdf._try_marker", _fake_marker)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4 fake")
        path = f.name
    try:
        result = await pdf_block.execute({"file_path": path}, {"use_marker": True})
        assert result["status"] == "success"
        assert result["result"]["text"] == "# Markdown from Marker"
        assert result["result"]["pages"] == 3
        assert result["result"]["engine"] == "marker"
    finally:
        os.unlink(path)


@pytest.mark.asyncio
async def test_pdf_block_falls_back_when_marker_unavailable(pdf_block, monkeypatch):
    """When Marker is unavailable, use_marker=true falls through to other engines."""
    monkeypatch.setattr("app.blocks.pdf._try_marker", lambda path: None)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4 fake")
        path = f.name
    try:
        result = await pdf_block.execute({"file_path": path}, {"use_marker": True})
        # The fake PDF cannot be parsed by pdfplumber/PyPDF2/PyMuPDF,
        # so we expect an error, but it should be a parser error not a Marker error.
        assert result["status"] == "error"
        error = str(result.get("result", {}).get("error", ""))
        assert "Marker" not in error
    finally:
        os.unlink(path)
