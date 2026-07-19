"""Tests for TenantBlock — tenant/project isolation."""

import pytest

from app.blocks.memory import MemoryBlock
from app.blocks.tenant_block import TenantBlock


@pytest.fixture
async def tenant_block():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = TenantBlock()
    block.memory_block = memory
    await block._legacy_initialize()
    return block


@pytest.mark.asyncio
async def test_create_tenant():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = TenantBlock()
    block.memory_block = memory
    await block._legacy_initialize()

    result = await block.process({"action": "create_tenant", "name": "Acme Corp"})
    assert result["status"] == "success"
    assert result["tenant"]["name"] == "Acme Corp"
    assert "tenant_id" in result["tenant"]


@pytest.mark.asyncio
async def test_get_tenant():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = TenantBlock()
    block.memory_block = memory
    await block._legacy_initialize()

    created = await block.process({"action": "create_tenant", "name": "Acme Corp"})
    tenant_id = created["tenant"]["tenant_id"]

    result = await block.process({"action": "get_tenant", "tenant_id": tenant_id})
    assert result["status"] == "success"
    assert result["tenant"]["tenant_id"] == tenant_id


@pytest.mark.asyncio
async def test_list_tenants():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = TenantBlock()
    block.memory_block = memory
    await block._legacy_initialize()

    await block.process({"action": "create_tenant", "name": "Acme"})
    await block.process({"action": "create_tenant", "name": "Globex"})

    result = await block.process({"action": "list_tenants"})
    assert result["status"] == "success"
    assert len(result["tenants"]) == 2


@pytest.mark.asyncio
async def test_create_project_under_tenant():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = TenantBlock()
    block.memory_block = memory
    await block._legacy_initialize()

    tenant = await block.process({"action": "create_tenant", "name": "Acme"})
    tenant_id = tenant["tenant"]["tenant_id"]

    project = await block.process({
        "action": "create_project",
        "tenant_id": tenant_id,
        "name": "Site A",
    })
    assert project["status"] == "success"
    assert project["project"]["tenant_id"] == tenant_id
    assert project["project"]["name"] == "Site A"


@pytest.mark.asyncio
async def test_list_projects_filtered_by_tenant():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = TenantBlock()
    block.memory_block = memory
    await block._legacy_initialize()

    t1 = await block.process({"action": "create_tenant", "name": "Acme"})
    t2 = await block.process({"action": "create_tenant", "name": "Globex"})

    await block.process({"action": "create_project", "tenant_id": t1["tenant"]["tenant_id"], "name": "P1"})
    await block.process({"action": "create_project", "tenant_id": t2["tenant"]["tenant_id"], "name": "P2"})

    result = await block.process({
        "action": "list_projects",
        "tenant_id": t1["tenant"]["tenant_id"],
    })
    assert result["status"] == "success"
    assert len(result["projects"]) == 1
    assert result["projects"][0]["name"] == "P1"


@pytest.mark.asyncio
async def test_resolve_context_from_headers():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = TenantBlock()
    block.memory_block = memory
    await block._legacy_initialize()

    tenant = await block.process({"action": "create_tenant", "name": "Acme"})
    project = await block.process({
        "action": "create_project",
        "tenant_id": tenant["tenant"]["tenant_id"],
        "name": "Site A",
    })

    result = await block.process({
        "action": "resolve_context",
        "headers": {
            "X-Tenant-Id": tenant["tenant"]["tenant_id"],
            "X-Project-Id": project["project"]["project_id"],
            "X-User-Id": "user-42",
        },
    })
    assert result["status"] == "success"
    assert result["context"]["tenant_id"] == tenant["tenant"]["tenant_id"]
    assert result["context"]["project_id"] == project["project"]["project_id"]
    assert result["context"]["user_id"] == "user-42"
