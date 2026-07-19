"""Tests for neutral PlanExecutor step-handler registration."""

from __future__ import annotations

import pytest

from app.core.plan_executor import PlanExecutor, PlanExecutionError
from app.schemas.execution_plan import ExecutionPlan, PlanStep
from app.schemas.project_session import ProjectSession


class FakeBlock:
    async def process(self, data):
        return {"status": "success", "code": "print('hi')"}


@pytest.fixture
def session():
    return ProjectSession(id="test", project_id="p1", data={})


@pytest.mark.asyncio
async def test_unknown_step_raises(session):
    executor = PlanExecutor()
    plan = ExecutionPlan(steps=[PlanStep(type="nonexistent", output_key="out")])
    result = await executor.run(plan, session)
    assert result.status == "error"
    assert result.step_results[0].status == "error"


@pytest.mark.asyncio
async def test_register_custom_handler(session):
    executor = PlanExecutor()

    async def custom_handler(step, sess):
        return {"value": step.args.get("value", 0) * 2}

    executor.register_step_handler("custom_double", custom_handler)
    plan = ExecutionPlan(steps=[PlanStep(type="custom_double", output_key="out", args={"value": 21})])
    result = await executor.run(plan, session)
    assert result.status == "success"
    assert result.step_results[0].output == {"value": 42}
    assert session.data["out"] == {"value": 42}


@pytest.mark.asyncio
async def test_default_handlers_still_present(session):
    executor = PlanExecutor()
    handlers = executor.list_step_handlers()
    assert "compute_cpm" in handlers
    assert "resource_histogram" in handlers
    assert "gantt" in handlers
    assert "compress" in handlers
    assert "generate_code" in handlers


@pytest.mark.asyncio
async def test_register_overrides_existing_handler(session):
    executor = PlanExecutor()

    async def fake_cpm(step, sess):
        return {"mock": True}

    executor.register_step_handler("compute_cpm", fake_cpm)
    plan = ExecutionPlan(steps=[PlanStep(type="compute_cpm", output_key="cpm")])
    result = await executor.run(plan, session)
    assert result.status == "success"
    assert result.step_results[0].output == {"mock": True}


def test_plan_execution_error_is_raised_for_bad_step():
    executor = PlanExecutor()
    with pytest.raises(PlanExecutionError):
        # Use a direct call to exercise the error path.
        import asyncio
        asyncio.run(executor._run_step(PlanStep(type="missing", output_key="x"), ProjectSession(id="t", project_id="p", data={})))
