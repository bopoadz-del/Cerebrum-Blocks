"""CPM Engine block — thin wrapper over app.lib.pm_computations.

The real forward/backward pass, float, and critical-path logic lives in
``app.lib.pm_computations.compute_cpm``. This block exposes the same capability
under a block-store friendly name.
"""

from typing import Any, Dict, List, Optional

from app.core.universal_base import UniversalBlock


class CPMEngineBlock(UniversalBlock):
    auto_validate = False
    name = "cpm_engine"
    version = "1.0.0"
    description = "Critical Path Method engine: ES/EF/LS/LF, total/free float, critical path"
    layer = 3
    tags = ["domain", "construction", "schedule", "cpm", "critical-path"]
    requires = []

    default_config = {
        "calendar_work_weekdays": [0, 1, 2, 3, 4],
    }

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Run CPM over an activity network.

        Accepts either:
          * a raw ``CPMInput`` dict (recommended): ``{"activities": [...]}``
          * a list of activity dicts in ``input_data`` / ``params["activities"]``
        """
        params = params or {}
        data = input_data if isinstance(input_data, dict) else {}

        activities = data.get("activities") or params.get("activities") or []
        if not activities:
            return {"status": "error", "error": "No activities provided"}

        project_start = data.get("project_start") or params.get("project_start")

        try:
            from app.lib.pm_computations import compute_cpm
            from app.schemas.cpm import Activity, CPMInput, WorkCalendar

            def _coerce_activity(raw: Any) -> Activity:
                if isinstance(raw, Activity):
                    return raw
                if not isinstance(raw, dict):
                    raw = {"id": str(raw)}
                preds = raw.get("predecessors") or []
                normalized = []
                for p in preds:
                    if isinstance(p, str):
                        normalized.append({"predecessor_id": p})
                    elif isinstance(p, dict):
                        normalized.append(p)
                    else:
                        normalized.append({"predecessor_id": str(p)})
                raw = {**raw, "predecessors": normalized}
                return Activity(**raw)

            cpm_activities = [_coerce_activity(a) for a in activities]
            cal = WorkCalendar(
                work_weekdays=self.config.get(
                    "calendar_work_weekdays", [0, 1, 2, 3, 4]
                )
            )
            cpm_input = CPMInput(
                activities=cpm_activities,
                project_start=project_start,
                calendar=cal,
            )
            output = compute_cpm(cpm_input)
            return {
                "status": "success",
                "project_duration": output.project_duration,
                "project_finish": output.project_finish.isoformat()
                if output.project_finish
                else None,
                "critical_path": output.critical_path,
                "critical_percentage": output.critical_percentage,
                "near_critical": output.near_critical,
                "results": [r.model_dump() for r in output.results],
            }
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "error": f"CPM computation failed: {exc}"}
