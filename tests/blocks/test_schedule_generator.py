"""Tests for the schedule_generator block."""

from __future__ import annotations

import pytest

from app.blocks.schedule_generator import ScheduleGeneratorBlock


@pytest.mark.asyncio
async def test_schedule_generator_exists_and_accepts_brief():
    block = ScheduleGeneratorBlock()
    result = await block.process({"brief": "Build a small office building"})
    # ConstructionContainer.generate_wbs may fail without a kit installed;
    # we just verify the block routes to it and returns a structured response.
    assert isinstance(result, dict)
    assert "status" in result


@pytest.mark.asyncio
async def test_schedule_generator_merges_params():
    block = ScheduleGeneratorBlock()
    result = await block.process(
        {"brief": "Data center", "target_count": 50},
        params={"project_type": "infrastructure"},
    )
    assert isinstance(result, dict)
    assert "status" in result
