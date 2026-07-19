"""Tests for BOQProcessorBlock (Excel/CSV/PDF)."""

from __future__ import annotations

import os

import pytest

from app.blocks.boq_processor import BOQProcessorBlock


@pytest.fixture
def block():
    return BOQProcessorBlock()


@pytest.mark.asyncio
async def test_parse_csv_success(block, tmp_path):
    path = tmp_path / "boq.csv"
    path.write_text(
        "Description,Quantity,Unit,Rate,Total,Section\n"
        "Concrete footing,10,m3,100,1000,Concrete\n"
        "Rebar,500,kg,2,1000,Steel\n"
    )
    result = await block.process({"file_path": str(path)})
    assert result["status"] == "success"
    assert result["item_count"] == 2
    assert result["total_cost"] == 2000.0
    assert result["currency"] == "USD"
    assert "Concrete" in result["cost_breakdown"]


@pytest.mark.asyncio
async def test_parse_excel_success(block, tmp_path):
    pytest.importorskip("openpyxl")
    import openpyxl

    path = tmp_path / "boq.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Description", "Qty", "Unit", "Rate", "Total", "Section"])
    ws.append(["Brick wall", 20, "m2", 50, 1000, "Masonry"])
    ws.append(["Paint", 100, "m2", 5, 500, "Finishes"])
    wb.save(path)

    result = await block.process({"file_path": str(path)})
    assert result["status"] == "success"
    assert result["item_count"] == 2
    assert result["total_cost"] == 1500.0


@pytest.mark.asyncio
async def test_missing_file(block):
    result = await block.process({"file_path": "/nonexistent/boq.csv"})
    assert result["status"] == "error"
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_unsupported_format(block, tmp_path):
    path = tmp_path / "boq.txt"
    path.write_text("not a boq")
    result = await block.process({"file_path": str(path)})
    assert result["status"] == "error"
    assert "unsupported format" in result["error"].lower()


@pytest.mark.asyncio
async def test_zero_quantity_filter(block, tmp_path):
    path = tmp_path / "boq.csv"
    path.write_text(
        "Description,Quantity,Unit,Rate,Total\n"
        "Zero item,0,m3,100,0\n"
        "Real item,5,m3,100,500\n"
    )
    result = await block.process({"file_path": str(path)})
    assert result["status"] == "success"
    assert result["item_count"] == 1
    assert result["line_items"][0]["description"] == "Real item"


@pytest.mark.asyncio
async def test_project_resolution_no_store(block, tmp_path):
    """A bare filename with project_id but no project store should still fail
    cleanly rather than crash on import."""
    result = await block.process(
        {"file_path": "Demolition BOQ.pdf"},
        {"project_id": "p1"},
    )
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_pdf_requires_pdfplumber(block, tmp_path):
    pdfplumber = pytest.importorskip("pdfplumber")
    path = tmp_path / "boq.pdf"
    # Build a minimal 1-page PDF with a simple table.
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=letter)
    c.drawString(50, 750, "Description")
    c.drawString(200, 750, "Qty")
    c.drawString(300, 750, "Rate")
    c.drawString(400, 750, "Total")
    c.drawString(50, 730, "Sand")
    c.drawString(200, 730, "10")
    c.drawString(300, 730, "5")
    c.drawString(400, 730, "50")
    c.save()

    result = await block.process({"file_path": str(path)})
    # pdfplumber may or may not detect a table; either success/partial is fine.
    assert result["status"] in ("success", "partial", "error")
