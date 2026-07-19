"""Tests for AuditBlock ActionRun structured run tracking."""

import pytest

from app.blocks.audit import AuditBlock
from app.blocks.memory import MemoryBlock


@pytest.fixture
async def audit_block():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = AuditBlock()
    block.memory_block = memory
    block.database_block = None
    await block._legacy_initialize()
    return block


@pytest.mark.asyncio
async def test_record_action_run():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = AuditBlock()
    block.memory_block = memory
    block.database_block = None
    await block._legacy_initialize()

    result = await block.process({
        "action": "record_run",
        "request_id": "req-1",
        "tenant_id": "tnt-1",
        "project_id": "prj-1",
        "user_id": "user-1",
        "action_id": "boq_processor",
        "status": "success",
        "duration_ms": 120,
        "input_hash": "abc123",
        "evidence_count": 2,
        "output_meta": {"item_count": 5},
    })
    assert result["status"] == "success"
    assert "run_id" in result


@pytest.mark.asyncio
async def test_query_action_runs_by_tenant_and_status():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = AuditBlock()
    block.memory_block = memory
    block.database_block = None
    await block._legacy_initialize()

    await block.process({
        "action": "record_run",
        "request_id": "req-1",
        "tenant_id": "tnt-1",
        "action_id": "boq_processor",
        "status": "success",
    })
    await block.process({
        "action": "record_run",
        "request_id": "req-2",
        "tenant_id": "tnt-2",
        "action_id": "boq_processor",
        "status": "error",
    })

    result = await block.process({
        "action": "query_runs",
        "tenant_id": "tnt-1",
        "status": "success",
    })
    assert result["status"] == "success"
    assert len(result["runs"]) == 1
    assert result["runs"][0]["tenant_id"] == "tnt-1"


@pytest.mark.asyncio
async def test_get_action_run_by_id():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = AuditBlock()
    block.memory_block = memory
    block.database_block = None
    await block._legacy_initialize()

    recorded = await block.process({
        "action": "record_run",
        "request_id": "req-1",
        "tenant_id": "tnt-1",
        "action_id": "boq_processor",
        "status": "success",
    })
    run_id = recorded["run_id"]

    result = await block.process({"action": "get_run", "run_id": run_id})
    assert result["status"] == "success"
    assert result["run"]["run_id"] == run_id
