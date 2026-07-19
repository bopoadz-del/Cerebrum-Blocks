"""Schedule Generator block — thin wrapper over ConstructionContainer.generate_wbs.

This block exposes the deterministic WBS generator under a block-store friendly
name so it can be called by the orchestrator, plan executor, or external API.
"""

from typing import Any, Dict

from app.core.universal_base import UniversalBlock


class ScheduleGeneratorBlock(UniversalBlock):
    auto_validate = False
    name = "schedule_generator"
    version = "1.0.0"
    description = "Generate a CPM-ready L2 work breakdown structure from a project brief"
    layer = 3
    tags = ["domain", "construction", "schedule", "wbs", "l2"]
    requires = []

    default_config = {
        "default_target_count": 200,
    }

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Generate an L2 schedule.

        Input fields (passed in ``input_data`` or ``params``):
          * ``brief``: project description
          * ``project_type``: data_center, building, infrastructure, ...
          * ``target_count``: desired activity count (clamped 20..1000)
          * ``start_date``: ISO date string
          * ``procurement_lead_times``: optional list of long-lead items
          * ``target_milestones``: optional list of target milestones
        """
        params = params or {}
        data = input_data if isinstance(input_data, dict) else {}

        merged = {
            "brief": data.get("brief")
            or params.get("brief")
            or "Generic construction project.",
            "target_count": data.get("target_count")
            or params.get("target_count")
            or self.config.get("default_target_count", 200),
            "project_type": data.get("project_type") or params.get("project_type"),
            "start_date": data.get("start_date") or params.get("start_date"),
            "procurement_lead_times": data.get("procurement_lead_times")
            or params.get("procurement_lead_times")
            or [],
            "target_milestones": data.get("target_milestones")
            or params.get("target_milestones")
            or [],
        }

        try:
            from app.containers.construction import ConstructionContainer

            kwargs = {k: v for k, v in merged.items() if v is not None}
            result = await ConstructionContainer().generate_wbs(
                input_data=kwargs,
                params=kwargs,
            )
            return result
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "error": f"Schedule generation failed: {exc}"}
