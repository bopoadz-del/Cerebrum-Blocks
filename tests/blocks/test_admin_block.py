"""Tests for AdminBlock — diagnostics and operator tooling."""

import pytest

from app.blocks.admin_block import AdminBlock
from app.blocks.memory import MemoryBlock


@pytest.fixture
async def admin_block():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = AdminBlock()
    block.memory_block = memory
    await block._legacy_initialize()
    return block


@pytest.mark.asyncio
async def test_preflight_check():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = AdminBlock()
    block.memory_block = memory
    await block._legacy_initialize()

    result = await block.process({"action": "preflight"})
    assert result["status"] == "success"
    assert "checks" in result
    assert result["checks"]["memory"]["status"] == "ok"


@pytest.mark.asyncio
async def test_bulk_delete_keys():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = AdminBlock()
    block.memory_block = memory
    await block._legacy_initialize()

    await memory.process({"action": "set", "key": "temp:1", "value": 1})
    await memory.process({"action": "set", "key": "temp:2", "value": 2})
    await memory.process({"action": "set", "key": "keep:1", "value": 3})

    result = await block.process({"action": "bulk_delete", "prefix": "temp:"})
    assert result["status"] == "success"
    assert result["deleted"] == 2

    keys = await memory.process({"action": "keys"})
    assert "temp:1" not in keys["keys"]
    assert "keep:1" in keys["keys"]


@pytest.mark.asyncio
async def test_system_stats():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = AdminBlock()
    block.memory_block = memory
    await block._legacy_initialize()

    await memory.process({"action": "set", "key": "a", "value": 1})
    await memory.process({"action": "set", "key": "b", "value": 2})

    result = await block.process({"action": "stats"})
    assert result["status"] == "success"
    assert result["stats"]["memory"]["size"] == 2
