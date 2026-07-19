"""Tests for fasttrack_analyzer, manpower_planner, and schedule_excel_writer."""

from __future__ import annotations

import pytest

from app.blocks.fasttrack_analyzer import FastTrackAnalyzerBlock
from app.blocks.manpower_planner import ManpowerPlannerBlock
from app.blocks.schedule_excel_writer import ScheduleExcelWriterBlock


@pytest.mark.asyncio
async def test_fasttrack_analyzer_compresses():
    block = FastTrackAnalyzerBlock()
    activities = [
        {"id": "A", "name": "Start", "duration": 5, "predecessors": []},
        {"id": "B", "name": "End", "duration": 5, "predecessors": ["A"]},
    ]
    reductions = {"A": 2}
    result = await block.process({"activities": activities, "reductions": reductions})
    assert result["status"] == "success"
    assert result["days_saved"] == 2
    assert len(result["scenarios"]) == 3


@pytest.mark.asyncio
async def test_fasttrack_analyzer_requires_activities():
    block = FastTrackAnalyzerBlock()
    result = await block.process({"reductions": {"A": 1}})
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_manpower_planner_histogram():
    block = ManpowerPlannerBlock()
    activities = [
        {"id": "A", "name": "Start", "duration": 3, "predecessors": [], "resources": ["carpenter"]},
        {"id": "B", "name": "End", "duration": 2, "predecessors": ["A"], "resources": ["carpenter"]},
    ]
    result = await block.process({"activities": activities})
    assert result["status"] == "success"
    assert "periods" in result


@pytest.mark.asyncio
async def test_schedule_excel_writer_l2():
    block = ScheduleExcelWriterBlock()
    activities = [
        {"id": "A", "name": "Start", "duration": 3, "predecessors": [], "manpower": 2, "wbs": "1.1"},
        {"id": "B", "name": "End", "duration": 2, "predecessors": ["A"], "manpower": 1, "wbs": "1.2"},
    ]
    result = await block.process({"activities": activities, "meta": {"project": "Test", "currency": "USD"}})
    assert result["status"] == "success"
    assert result["format"] == "l2_cost_loaded"
    assert "l2_schedule.xlsx" in result["file_path"]


@pytest.mark.asyncio
async def test_schedule_excel_writer_requires_input():
    block = ScheduleExcelWriterBlock()
    result = await block.process({})
    assert result["status"] == "error"
