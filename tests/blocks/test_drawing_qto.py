"""Tests for DrawingQTOBlock."""

from __future__ import annotations

import os

import pytest

from app.blocks.drawing_qto import DrawingQTOBlock


@pytest.fixture
def block():
    return DrawingQTOBlock()


@pytest.mark.asyncio
async def test_missing_file(block):
    result = await block.process({"file_path": "/nonexistent/plan.dxf"})
    assert result["status"] == "error"
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_unsupported_format(block, tmp_path):
    path = tmp_path / "plan.pdf"
    path.write_text("not a dxf")
    result = await block.process({"file_path": str(path)})
    assert result["status"] == "error"
    assert ".dxf" in result["error"].lower() or ".dwg" in result["error"].lower()


@pytest.mark.asyncio
async def test_minimal_dxf_extraction(block, tmp_path):
    ezdxf = pytest.importorskip("ezdxf")

    path = tmp_path / "plan.dxf"
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_line((0, 0), (10, 0))
    doc.saveas(str(path))

    result = await block.process({"file_path": str(path)})
    assert result["status"] == "success"
    assert result["element_count"] >= 1
    assert result["total_area_m2"] >= 0
