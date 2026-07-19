"""Tests for BIMExtractorBlock."""

from __future__ import annotations

import os

import pytest

from app.blocks.bim_extractor import BIMExtractorBlock


@pytest.fixture
def block():
    return BIMExtractorBlock()


@pytest.mark.asyncio
async def test_missing_file(block):
    result = await block.process({"file_path": "/nonexistent/model.ifc"})
    assert result["status"] == "error"
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_unsupported_extension(block, tmp_path):
    path = tmp_path / "model.rvt"
    path.write_text("not an ifc")
    result = await block.process({"file_path": str(path)})
    assert result["status"] == "error"
    assert ".ifc" in result["error"]


@pytest.mark.asyncio
async def test_invalid_ifc_file(block, tmp_path):
    """A file with .ifc extension but invalid content should fail cleanly."""
    path = tmp_path / "model.ifc"
    path.write_text("not a valid ifc file")
    result = await block.process({"file_path": str(path)})
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_bytes_input(block):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    data = b"not valid ifc bytes"
    result = await block.process(data)
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_minimal_ifc_extraction(block, tmp_path):
    ifcopenshell = pytest.importorskip("ifcopenshell")

    path = tmp_path / "model.ifc"
    model = ifcopenshell.file(schema="IFC4")
    project = model.create_entity("IfcProject", GlobalId="0PROJECT", Name="Demo")
    wall = model.create_entity(
        "IfcWall",
        GlobalId="WALL001",
        Name="Wall 1",
        Description="A test wall",
    )
    model.write(str(path))

    result = await block.process({"file_path": str(path)})
    assert result["status"] == "success"
    assert result["element_count"] >= 1
    assert any(e["ifc_type"] == "IfcWall" for e in result["building_elements"])
    assert result["project_info"]["name"] == "Demo"
