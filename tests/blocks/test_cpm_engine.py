"""Tests for the cpm_engine block."""

from __future__ import annotations

import pytest

from app.blocks.cpm_engine import CPMEngineBlock


@pytest.mark.asyncio
async def test_cpm_engine_computes_critical_path():
    block = CPMEngineBlock()
    activities = [
        {"id": "A", "name": "Start", "duration": 3, "predecessors": []},
        {"id": "B", "name": "Middle", "duration": 5, "predecessors": ["A"]},
        {"id": "C", "name": "End", "duration": 2, "predecessors": ["B"]},
    ]
    result = await block.process({"activities": activities})
    assert result["status"] == "success"
    assert result["project_duration"] == 10
    assert result["critical_path"] == ["A", "B", "C"]


@pytest.mark.asyncio
async def test_cpm_engine_requires_activities():
    block = CPMEngineBlock()
    result = await block.process({})
    assert result["status"] == "error"
    assert "No activities" in result["error"]
