"""Tests for AuthBlock tenancy support."""

import pytest

from app.blocks.auth import AuthBlock, Role
from app.blocks.memory import MemoryBlock


@pytest.fixture
async def auth_block():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = AuthBlock(config={"master_key": "test-master"})
    block.memory_block = memory
    await block._legacy_initialize()
    return block


@pytest.mark.asyncio
async def test_create_key_with_tenant_and_project():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = AuthBlock(config={"master_key": "test-master"})
    block.memory_block = memory
    await block._legacy_initialize()

    result = await block.process({
        "action": "create_key",
        "name": "scoped-key",
        "role": "pro",
        "owner": "user-1",
        "tenant_id": "tenant-1",
        "project_id": "project-1",
    })
    assert "api_key" in result

    validation = await block.process({
        "action": "validate",
        "api_key": result["api_key"],
    })
    assert validation["valid"] is True
    assert validation["tenant_id"] == "tenant-1"
    assert validation["project_id"] == "project-1"


@pytest.mark.asyncio
async def test_validate_returns_none_tenant_for_unscoped_key():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = AuthBlock(config={"master_key": "test-master"})
    block.memory_block = memory
    await block._legacy_initialize()

    key = await block.process({
        "action": "create_key",
        "name": "legacy-key",
        "role": "admin",
        "owner": "user-1",
    })

    validation = await block.process({
        "action": "validate",
        "api_key": key["api_key"],
    })
    assert validation["valid"] is True
    assert validation.get("tenant_id") is None
    assert validation.get("project_id") is None


@pytest.mark.asyncio
async def test_check_permission_with_tenant_context():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = AuthBlock(config={"master_key": "test-master"})
    block.memory_block = memory
    await block._legacy_initialize()

    key = await block.process({
        "action": "create_key",
        "name": "scoped-key",
        "role": "pro",
        "owner": "user-1",
        "tenant_id": "tenant-1",
        "project_id": "project-1",
    })

    result = await block.process({
        "action": "check_permission",
        "api_key": key["api_key"],
        "block": "storage",
    })
    assert result["allowed"] is True
    assert result["tenant_id"] == "tenant-1"
    assert result["project_id"] == "project-1"
