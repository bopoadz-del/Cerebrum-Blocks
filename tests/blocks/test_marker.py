"""Tests for Marker PDF Block."""

import os
import sys
import tempfile

import pytest

from app.blocks import MarkerBlock
from app.blocks.marker import _try_marker


@pytest.fixture
def marker_block():
    return MarkerBlock()


@pytest.mark.asyncio
async def test_marker_block_metadata(marker_block):
    assert marker_block.name == "marker"
    assert marker_block.version == "1.0.0"
    assert "pdf" in marker_block.tags
    assert "markdown" in marker_block.tags


@pytest.mark.asyncio
async def test_marker_block_file_not_found(marker_block):
    result = await marker_block.execute(
        {"file_path": "/tmp/definitely_not_real.pdf"},
        {},
    )
    assert result["status"] == "error"
    inner = result.get("result", {})
    assert "File not found" in str(inner.get("error", ""))


def test_try_marker_returns_none_when_not_installed(monkeypatch):
    """If marker-pdf is not importable, _try_marker returns None gracefully."""
    monkeypatch.setitem(sys.modules, "marker.converters.pdf", None)
    result = _try_marker("/tmp/any.pdf")
    assert result is None


@pytest.mark.asyncio
async def test_marker_block_missing_dependency(marker_block, monkeypatch):
    """When marker-pdf is not importable the block returns a helpful error."""
    monkeypatch.setitem(sys.modules, "marker.converters.pdf", None)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4 fake")
        path = f.name
    try:
        result = await marker_block.execute({"file_path": path}, {})
        assert result["status"] == "error"
        inner = result.get("result", {})
        assert "marker-pdf is not installed" in str(inner.get("error", ""))
    finally:
        os.unlink(path)


@pytest.mark.asyncio
async def test_marker_block_success_when_installed(marker_block, monkeypatch):
    """If Marker is installed, the block should return its result envelope."""

    def _fake_marker(path):
        return {"text": "# Hello\n\nWorld", "pages": 2}

    monkeypatch.setattr("app.blocks.marker._try_marker", _fake_marker)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4 fake")
        path = f.name
    try:
        result = await marker_block.execute({"file_path": path}, {})
        assert result["status"] == "success"
        assert result["result"]["text"] == "# Hello\n\nWorld"
        assert result["result"]["pages"] == 2
        assert result["result"]["engine"] == "marker"
    finally:
        os.unlink(path)
