"""Tests for SmartOrchestratorBlock routing."""

from __future__ import annotations

import pytest

from app.blocks.smart_orchestrator import SmartOrchestratorBlock


@pytest.fixture
def block():
    return SmartOrchestratorBlock()


@pytest.mark.asyncio
async def test_routes_boq_message(block):
    result = await block.process({"text": "analyze the BOQ spreadsheet"})
    assert result["status"] == "success"
    assert "boq_process" in result["action_queue"]


@pytest.mark.asyncio
async def test_routes_safety_message(block):
    result = await block.process({"text": "run a site safety audit"})
    assert result["status"] == "success"
    assert "safety_compliance_audit" in result["action_queue"]


@pytest.mark.asyncio
async def test_file_type_hint_xer(block):
    result = await block.process({"file_path": "schedule.xer"})
    assert result["status"] == "success"
    assert result["file_type_hint"] == ".xer"
    assert "parse_primavera_schedule" in result["action_queue"]


@pytest.mark.asyncio
async def test_list_actions(block):
    result = await block.process({"text": "list actions"})
    assert result["status"] == "success"
    assert result["total_actions"] > 40
    assert "boq_process" in result["all_actions"]


@pytest.mark.asyncio
async def test_unknown_message_uses_fallback(block):
    result = await block.process({"text": "flibbertigibbet"})
    assert result["status"] == "success"
    assert len(result["action_queue"]) == 1
    assert result["action_queue"][0] == block.config.get("fallback_agent", "intelligent_workflow")
