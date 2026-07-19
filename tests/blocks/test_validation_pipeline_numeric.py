"""Tests for the numeric ValidationPipelineBlock (Fork-derived)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.blocks.validation_pipeline import ValidationPipelineBlock


@pytest.fixture
def block():
    return ValidationPipelineBlock()


@pytest.mark.asyncio
async def test_syntactic_failure_on_none(block):
    result = await block.process({"value": None})
    assert result["overall"] == "fail"
    assert result["first_failure"] == "syntactic"


@pytest.mark.asyncio
async def test_dimensional_check_passes(block):
    result = await block.process({"value": 5.9, "unit": "degC"})
    assert result["overall"] == "pass"
    assert result["stages"]["dimensional"]["pass"] is True


@pytest.mark.asyncio
async def test_physical_check_fails_negative(block):
    result = await block.process({"value": -5, "unit": "m3"})
    assert result["overall"] == "fail"
    assert result["first_failure"] == "physical"


@pytest.mark.asyncio
async def test_empirical_range_from_context(block, tmp_path, monkeypatch):
    result = await block.process(
        {"value": 150},
        params={
            "context": {
                "empirical_min": 100,
                "empirical_max": 200,
            }
        },
    )
    assert result["overall"] == "pass"


@pytest.mark.asyncio
async def test_empirical_range_fail(block, tmp_path, monkeypatch):
    result = await block.process(
        {"value": 999},
        params={
            "context": {
                "empirical_min": 100,
                "empirical_max": 200,
            }
        },
    )
    assert result["overall"] == "fail"
    assert result["first_failure"] == "empirical"


@pytest.mark.asyncio
async def test_operational_check(block):
    result = await block.process(
        {"value": 10},
        params={"context": {"duration_weeks": 16, "available_weeks": 8}},
    )
    assert result["overall"] == "fail"
    assert result["first_failure"] == "operational"


@pytest.mark.asyncio
async def test_temperature_physical_negative_allowed(block):
    result = await block.process(
        {"value": -10, "unit": "degC"},
        params={"context": {"material_type": "concrete", "metric": "temperature_degc"}},
    )
    assert result["overall"] == "pass"


@pytest.mark.asyncio
async def test_blank_input_error(block):
    result = await block.process({}, params={})
    assert result["status"] == "error"
