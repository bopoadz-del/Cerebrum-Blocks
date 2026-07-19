"""Tests for SpecAnalyzerBlock."""

from __future__ import annotations

import pytest

from app.blocks.spec_analyzer import SpecAnalyzerBlock


SAMPLE_SPEC = """
SECTION 1 - CONCRETE WORK
Concrete shall be of class C30/37.
Reinforcing steel shall be Grade 60 bars conforming to ASTM A615.
All materials shall comply with ACI 318.
Submittal required for concrete mix design.
Minimum requirement: cover shall not be less than 40 mm.
"""


@pytest.fixture
def block():
    return SpecAnalyzerBlock()


@pytest.mark.asyncio
async def test_raw_text_extraction(block):
    result = await block.process({"text": SAMPLE_SPEC})
    assert result["status"] == "success"
    assert result["sections_found"] >= 1

    types = {g["type"]: g for g in result["grade_requirements"]}
    assert "concrete_strength_mpa" in types or any("C30" in g.get("value", "") for g in result["grade_requirements"])
    assert any("A615" in g.get("value", "") for g in result["grade_requirements"])

    assert any(m["material_type"] == "concrete" for m in result["material_specs"])
    assert any(m["material_type"] == "rebar" for m in result["material_specs"])

    assert any(f["flag_type"] == "compliance" for f in result["compliance_flags"])
    assert any(f["flag_type"] == "submittal" for f in result["compliance_flags"])

    assert any("ASTM A615" in s.get("value", "") or "A615" in s.get("value", "") for s in result["standards_referenced"])


@pytest.mark.asyncio
async def test_missing_input(block):
    result = await block.process({})
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_file_not_found(block):
    result = await block.process({"file_path": "/nonexistent/spec.pdf"})
    assert result["status"] == "error"
    assert "not found" in result["error"].lower()
