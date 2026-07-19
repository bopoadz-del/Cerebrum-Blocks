"""Tests for construction-specific plan executor handlers."""

from __future__ import annotations

import pytest

from app.containers.construction.plan_handlers import register_construction_handlers
from app.core.plan_executor import PlanExecutor
from app.schemas.execution_plan import ExecutionPlan, PlanStep
from app.schemas.project_session import ProjectSession


@pytest.fixture
def session():
    return ProjectSession(id="test", project_id="p1", data={})


def test_registration_adds_construction_steps():
    executor = PlanExecutor()
    register_construction_handlers(executor)
    handlers = executor.list_step_handlers()
    assert "extract_document" in handlers
    assert "build_wbs" in handlers
    assert "cost_load" in handlers
    assert "render_artifact" in handlers


@pytest.mark.asyncio
async def test_extract_document_without_schedule_feed(session):
    """If schedule_feed lib is missing, the handler raises a clear error."""
    executor = PlanExecutor()
    register_construction_handlers(executor)
    plan = ExecutionPlan(steps=[PlanStep(type="extract_document", output_key="feed")])
    result = await executor.run(plan, session)
    assert result.status == "error"
    assert "schedule_feed" in result.step_results[0].error.lower()
