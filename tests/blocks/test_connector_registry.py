"""Tests for ConnectorRegistryBlock — connector lifecycle management."""

import pytest

from app.blocks.connector_registry import ConnectorRegistryBlock
from app.blocks.memory import MemoryBlock


@pytest.fixture
async def registry():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = ConnectorRegistryBlock()
    block.memory_block = memory
    await block._legacy_initialize()
    return block


@pytest.mark.asyncio
async def test_register_connector():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = ConnectorRegistryBlock()
    block.memory_block = memory
    await block._legacy_initialize()

    result = await block.process({
        "action": "register",
        "connector_id": "mock_erp",
        "name": "Mock ERP",
        "schema": {
            "base_url": "https://erp.example.com",
            "auth_type": "api_key",
        },
    })
    assert result["status"] == "success"
    assert result["connector"]["connector_id"] == "mock_erp"
    assert result["connector"]["status"] == "registered"


@pytest.mark.asyncio
async def test_get_connector():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = ConnectorRegistryBlock()
    block.memory_block = memory
    await block._legacy_initialize()

    await block.process({
        "action": "register",
        "connector_id": "mock_erp",
        "name": "Mock ERP",
        "schema": {"base_url": "https://erp.example.com"},
    })

    result = await block.process({"action": "get", "connector_id": "mock_erp"})
    assert result["status"] == "success"
    assert result["connector"]["name"] == "Mock ERP"


@pytest.mark.asyncio
async def test_list_connectors():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = ConnectorRegistryBlock()
    block.memory_block = memory
    await block._legacy_initialize()

    await block.process({"action": "register", "connector_id": "a", "name": "A"})
    await block.process({"action": "register", "connector_id": "b", "name": "B"})

    result = await block.process({"action": "list"})
    assert result["status"] == "success"
    assert len(result["connectors"]) == 2


@pytest.mark.asyncio
async def test_update_connector_status():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = ConnectorRegistryBlock()
    block.memory_block = memory
    await block._legacy_initialize()

    await block.process({"action": "register", "connector_id": "mock_erp", "name": "Mock ERP"})
    result = await block.process({
        "action": "update_status",
        "connector_id": "mock_erp",
        "status": "healthy",
        "last_tested": "2026-07-19T00:00:00Z",
    })
    assert result["status"] == "success"
    assert result["connector"]["status"] == "healthy"
