"""Construction-specific plan-executor step handlers.

These handlers extend ``app.core.plan_executor.PlanExecutor`` with schedule
workflow steps. They are registered from the construction kit rather than
living in the core, keeping the core executor domain-neutral.
"""

from __future__ import annotations

import os
import tempfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.plan_executor import PlanExecutor
    from app.schemas.execution_plan import PlanStep
    from app.schemas.project_session import ProjectSession


def register_construction_handlers(executor: "PlanExecutor") -> None:
    """Register construction workflow step handlers on a PlanExecutor."""
    executor.register_step_handler("extract_document", _step_extract_document)
    executor.register_step_handler("build_wbs", _step_build_wbs)
    executor.register_step_handler("cost_load", _step_cost_load)
    executor.register_step_handler("render_artifact", _step_render_artifact)


async def _step_extract_document(step: "PlanStep", session: "ProjectSession"):
    """document_engine over RFP/BOD docs -> real lead times + milestones."""
    try:
        from app.core import projects as projects_store
    except ImportError as exc:
        raise PlanExecutionError(
            "schedule_feed library is not available; install the construction kit"
        ) from exc

    try:
        from app.lib.schedule_feed import extract_schedule_feed
    except ImportError as exc:
        raise PlanExecutionError(
            "schedule_feed library is not available; install the construction kit"
        ) from exc

    doc_ids = step.args.get("document_ids") or []
    documents = [
        doc for did in doc_ids
        if (doc := projects_store.get_document(did))
    ]
    lead_times, milestones = await extract_schedule_feed(documents)
    session.data["procurement_lead_times"] = lead_times
    session.data["target_milestones"] = milestones
    value = {"lead_times": lead_times, "target_milestones": milestones}
    session.data[step.output_key or "schedule_feed"] = value
    return value


async def _step_build_wbs(step: "PlanStep", session: "ProjectSession"):
    """generate_wbs, consuming any lead times/milestones the extract step
    staged. Writes the WBS + its activities into the session."""
    try:
        from app.containers.construction import ConstructionContainer
    except ImportError as exc:
        raise PlanExecutionError(
            "ConstructionContainer is not available"
        ) from exc

    params = {
        "brief": step.args.get("brief") or "",
        "target_count": step.args.get("target_count", 200),
        "project_type": step.args.get("project_type"),
        "start_date": step.args.get("start_date"),
        "procurement_lead_times": session.data.get("procurement_lead_times") or [],
        "target_milestones": session.data.get("target_milestones") or [],
    }
    wbs = await ConstructionContainer().generate_wbs({}, params)
    session.data["wbs"] = wbs
    session.data["activities"] = wbs.get("activities") or []
    value = {
        "actual_count": wbs.get("actual_count"),
        "duration_days": (wbs.get("summary") or {}).get("total_duration_days"),
        "procurement_injected": wbs.get("procurement_injected"),
    }
    session.data[step.output_key or "wbs_summary"] = value
    return value


async def _step_cost_load(step: "PlanStep", session: "ProjectSession"):
    """Bridge the WBS -> cost-loaded workbook and stage it in the session."""
    try:
        from app.lib.schedule_bridge import bridge_wbs_to_cost_loaded
        from app.lib.pm_excel import generate_cost_loaded_schedule
    except ImportError as exc:
        raise PlanExecutionError(
            "schedule_bridge/pm_excel libraries are not available; install the construction kit"
        ) from exc

    wbs = session.data.get("wbs") or {}
    acts = wbs.get("activities") or session.data.get("activities") or []
    if not acts:
        raise PlanExecutionError("no WBS activities staged — run build_wbs first")

    day_rate = step.args.get("day_rate")
    bridged = bridge_wbs_to_cost_loaded(
        acts,
        crew_per_trade=step.args.get("crew_per_trade", 4),
        day_rate=day_rate,
    )
    meta = {
        "project": step.args.get("project_name") or "Project",
        "currency": step.args.get("currency", "USD"),
    }
    sd = step.args.get("start_date") or wbs.get("start_date")
    if sd:
        meta["start_date"] = sd
    if day_rate:
        meta["cost_basis"] = "Indicative Labor"
    milestones = session.data.get("target_milestones") or []
    if milestones:
        meta["target_milestones"] = milestones

    wb = generate_cost_loaded_schedule(meta, bridged)
    fd, path = tempfile.mkstemp(prefix="sched_plan_", suffix=".xlsx")
    os.close(fd)
    wb.save(path)
    total_mandays = sum(
        int(a.get("manpower", 0) or 0) * int(a.get("duration", 0) or 0)
        for a in bridged
    )
    summary = {
        "duration_days": (wbs.get("summary") or {}).get("total_duration_days"),
        "critical_count": (wbs.get("summary") or {}).get("critical_count"),
        "procurement_injected": wbs.get("procurement_injected", 0),
        "activities": wbs.get("actual_count") or len(acts),
        "total_man_days": total_mandays,
        "target_milestones": milestones,
    }
    session.data["schedule_workbook_path"] = path
    session.data["schedule_summary"] = summary
    session.data[step.output_key or "cost_load"] = summary
    return summary


async def _step_render_artifact(step: "PlanStep", session: "ProjectSession"):
    """Materialize the staged workbook as a session artifact."""
    from app.schemas.project_session import Artifact

    path = session.data.get("schedule_workbook_path")
    if not path:
        raise PlanExecutionError("no staged workbook — run cost_load first")
    name = step.args.get("name") or "Schedule.xlsx"
    art = Artifact(name=name, path=path, type=step.args.get("type", "excel"))
    session.artifacts.append(art)
    value = {"name": name, "path": path, "type": art.type}
    session.data[step.output_key or "artifact"] = value
    return value


class PlanExecutionError(Exception):
    """A construction plan step could not run."""
