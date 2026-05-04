"""Tests for Workflow Block."""

import pytest
from app.blocks import WorkflowBlock


@pytest.fixture
def workflow_block():
    return WorkflowBlock()


@pytest.mark.asyncio
async def test_workflow_block_execute_structure(workflow_block):
    """Test standardized JSON structure."""
    result = await workflow_block.execute(
        {
            "pipeline_id": "test-pipe",
            "steps": [
                {"id": "s1", "block": "chat", "input": {"text": "hello"}, "params": {}}
            ],
        },
        {"action": "run"},
    )
    assert "block" in result
    assert result["block"] == "workflow"
    assert "request_id" in result
    assert "status" in result
    assert "result" in result
    assert "confidence" in result
    assert "metadata" in result
    assert "source_id" in result
    assert "processing_time_ms" in result


@pytest.mark.asyncio
async def test_workflow_block_metadata(workflow_block):
    assert workflow_block.name == "workflow"
    assert workflow_block.config.version == "1.0.0"
    assert workflow_block.config.requires_api_key == False


@pytest.mark.asyncio
async def test_workflow_empty_steps(workflow_block):
    result = await workflow_block.execute(
        {"pipeline_id": "empty", "steps": []},
        {"action": "run"},
    )
    inner = result.get("result", result)
    assert inner.get("status") == "error"


@pytest.mark.asyncio
async def test_workflow_variable_interpolation(workflow_block):
    context = {
        "pipeline_id": "test",
        "steps": {
            "step1": {"result": {"text": "Hello World"}}
        },
    }
    step_input = {"text": "{{steps.step1.result.text}}"}
    interpolated = workflow_block._interpolate(step_input, context)
    assert interpolated["text"] == "Hello World"


@pytest.mark.asyncio
async def test_workflow_list_and_get(workflow_block):
    # Register a pipeline
    await workflow_block.execute(
        {"pipeline_id": "demo", "steps": [{"id": "s1", "block": "chat", "input": {}}]},
        {"action": "run"},
    )
    list_result = await workflow_block.execute(None, {"action": "list"})
    assert list_result["result"]["status"] == "success"

    get_result = await workflow_block.execute("demo", {"action": "get"})
    assert get_result["result"]["status"] == "success"


@pytest.mark.asyncio
async def test_workflow_history(workflow_block):
    result = await workflow_block.execute(None, {"action": "history"})
    assert result["result"]["status"] == "success"
    assert "runs" in result["result"]


@pytest.mark.asyncio
async def test_workflow_cron_parser(workflow_block):
    assert workflow_block._cron_next_wait("*/5 * * * *") == 300
    assert workflow_block._cron_next_wait("*/10 * * * *") == 600
    assert workflow_block._cron_next_wait("bad") == 300  # fallback
