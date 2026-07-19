"""Tests for PrimaveraParserBlock."""

from __future__ import annotations

import pytest

from app.blocks.primavera_parser import PrimaveraParserBlock


MINIMAL_XER = """%T	PROJECT
%F	proj_id	proj_short_name	plan_start_date	scd_end_date	status_code
%R	P1	Demo Project	2024-01-01 08:00	2024-02-01 17:00	Active
%T	TASK
%F	task_id	task_code	task_name	task_type	status_code	early_start_date	early_end_date	target_drtn_hr_cnt	total_float_hr_cnt	phys_complete_pct	wbs_id
%R	100	A1010	Start	TT_Task	Not Started	2024-01-01 08:00	2024-01-05 17:00	40	0	0	W1
%R	200	A1020	Finish	TT_Task	Not Started	2024-01-08 08:00	2024-01-12 17:00	40	0	0	W1
%T	TASKPRED
%F	task_id	pred_task_id	pred_type	lag_hr_cnt
%R	200	100	PR_FS	0
%T	RSRC
%F	rsrc_id	rsrc_name	rsrc_short_name	rsrc_type	unit_id
%R	R1	Labor Crew	LC	Labour	day
%E
"""


@pytest.fixture
def block():
    return PrimaveraParserBlock()


@pytest.fixture
def xer_path(tmp_path):
    path = tmp_path / "schedule.xer"
    path.write_text(MINIMAL_XER, encoding="cp1252")
    return str(path)


@pytest.mark.asyncio
async def test_missing_file(block):
    result = await block.process({"file_path": "/nonexistent/schedule.xer"})
    assert result["status"] == "error"
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_wrong_extension(block, tmp_path):
    path = tmp_path / "schedule.txt"
    path.write_text(MINIMAL_XER, encoding="cp1252")
    result = await block.process({"file_path": str(path)})
    assert result["status"] == "error"
    assert ".xer" in result["error"].lower()


@pytest.mark.asyncio
async def test_parse_minimal_xer(block, xer_path):
    result = await block.process({"file_path": xer_path})
    assert result["status"] == "success"
    assert result["activity_count"] == 2
    data = result["schedule_data"]
    assert data["activity_count"] == 2
    assert data["resource_definition_count"] == 1
    assert data["project_start"] == "2024-01-01"
    assert data["project_finish"] == "2024-01-12"
    assert "cpm" in result
    assert result["cpm"]["total_duration_days"] >= 9


@pytest.mark.asyncio
async def test_caps_respected(block, xer_path):
    result = await block.process(
        {"file_path": xer_path},
        {"max_activities": 1, "max_resources": 0},
    )
    assert result["status"] == "success"
    assert len(result["activities"]) == 1
    assert len(result["resource_definitions"]) == 1


@pytest.mark.asyncio
async def test_bytes_input(block, tmp_path):
    data = MINIMAL_XER.encode("cp1252")
    result = await block.process(data)
    assert result["status"] == "success"
    assert result["activity_count"] == 2
