"""Tests for AgentCatalogBlock — declarative agent manifests and composition."""

import pytest

from app.blocks.agent_catalog import AgentCatalogBlock
from app.blocks.memory import MemoryBlock


@pytest.fixture
async def catalog():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = AgentCatalogBlock()
    block.memory_block = memory
    await block._legacy_initialize()
    return block


@pytest.mark.asyncio
async def test_create_manifest():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = AgentCatalogBlock()
    block.memory_block = memory
    await block._legacy_initialize()

    manifest = {
        "manifest_id": "construction-pm",
        "name": "Construction PM Agent",
        "description": "PM agent for construction projects",
        "base_agent": "reasoner",
        "hats": ["pm", "scheduler"],
        "activation_triggers": ["schedule", "plan", "cpm"],
        "handoff_rules": [{"to": "safety-expert", "trigger": "safety"}],
        "playbook": {"standards": ["PMBOK"], "procedures": ["monthly-report"]},
        "memory_policy": {"save": ["decisions"], "ttl_seconds": 86400},
    }
    result = await block.process({"action": "create_manifest", "manifest": manifest})
    assert result["status"] == "success"
    assert result["manifest"]["manifest_id"] == "construction-pm"


@pytest.mark.asyncio
async def test_get_manifest():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = AgentCatalogBlock()
    block.memory_block = memory
    await block._legacy_initialize()

    manifest = {
        "manifest_id": "construction-pm",
        "name": "Construction PM Agent",
        "base_agent": "reasoner",
        "hats": ["pm"],
    }
    await block.process({"action": "create_manifest", "manifest": manifest})

    result = await block.process({"action": "get_manifest", "manifest_id": "construction-pm"})
    assert result["status"] == "success"
    assert result["manifest"]["name"] == "Construction PM Agent"


@pytest.mark.asyncio
async def test_resolve_agent_by_trigger():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = AgentCatalogBlock()
    block.memory_block = memory
    await block._legacy_initialize()

    manifest = {
        "manifest_id": "construction-pm",
        "name": "Construction PM Agent",
        "base_agent": "reasoner",
        "hats": ["pm", "scheduler"],
        "activation_triggers": ["schedule", "plan"],
    }
    await block.process({"action": "create_manifest", "manifest": manifest})

    result = await block.process({"action": "resolve", "message": "update the schedule"})
    assert result["status"] == "success"
    assert result["manifest_id"] == "construction-pm"
    assert "pm" in result["hats"]


@pytest.mark.asyncio
async def test_validate_composition_requires_base_agent():
    memory = MemoryBlock(None, {"max_size": 1000, "default_ttl": 3600})
    block = AgentCatalogBlock()
    block.memory_block = memory
    await block._legacy_initialize()

    manifest = {"manifest_id": "bad", "name": "Bad Agent"}
    result = await block.process({"action": "create_manifest", "manifest": manifest})
    assert result["status"] == "error"
    assert "base_agent" in result["error"]
