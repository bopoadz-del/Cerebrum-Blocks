"""Tests for GraphOrchestratorBlock — universal directed-graph execution."""

import pytest

from app.blocks.graph_orchestrator import GraphOrchestratorBlock


@pytest.fixture
def orchestrator():
    return GraphOrchestratorBlock()


@pytest.mark.asyncio
async def test_linear_graph_execution(orchestrator):
    graph = {
        "nodes": {
            "start": {"block": "_identity", "config": {"add": 1}},
            "middle": {"block": "_identity", "config": {"add": 10}},
            "end": {"block": "_identity", "config": {"add": 100}},
        },
        "edges": [
            {"from": "start", "to": "middle"},
            {"from": "middle", "to": "end"},
        ],
        "entry": "start",
    }

    result = await orchestrator.process(
        {"graph": graph, "state": {"value": 0}},
        {"action": "execute"},
    )
    assert result["status"] == "success"
    assert result["state"]["value"] == 111
    assert [n["node"] for n in result["trace"]] == ["start", "middle", "end"]


@pytest.mark.asyncio
async def test_conditional_edge_execution(orchestrator):
    graph = {
        "nodes": {
            "start": {"block": "_identity", "config": {"set_flag": True}},
            "yes": {"block": "_identity", "config": {"add": 1}},
            "no": {"block": "_identity", "config": {"add": 100}},
        },
        "edges": [
            {"from": "start", "to": "yes", "condition": "state.flag"},
            {"from": "start", "to": "no", "condition": "not state.flag"},
        ],
        "entry": "start",
    }

    result = await orchestrator.process(
        {"graph": graph, "state": {"value": 0}},
        {"action": "execute"},
    )
    assert result["status"] == "success"
    assert result["state"]["value"] == 1
    assert "yes" in [n["node"] for n in result["trace"]]
    assert "no" not in [n["node"] for n in result["trace"]]


@pytest.mark.asyncio
async def test_missing_entry_node_returns_error(orchestrator):
    graph = {
        "nodes": {"a": {"block": "_identity"}},
        "edges": [],
    }
    result = await orchestrator.process(
        {"graph": graph, "state": {}},
        {"action": "execute"},
    )
    assert result["status"] == "error"
    assert "entry" in result["error"].lower()


@pytest.mark.asyncio
async def test_invalid_edge_target_returns_error(orchestrator):
    graph = {
        "nodes": {"a": {"block": "_identity"}},
        "edges": [{"from": "a", "to": "missing"}],
        "entry": "a",
    }
    result = await orchestrator.process(
        {"graph": graph, "state": {}},
        {"action": "execute"},
    )
    assert result["status"] == "error"
    assert "missing" in result["error"]
