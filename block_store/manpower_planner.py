"""Manpower Planner block — thin wrapper over app.lib.pm_computations.

The trade-based resource histogram lives in
``app.lib.pm_computations.resource_histogram``. This block exposes the same
capability under a block-store friendly name.
"""

from typing import Any, Dict, List

from app.core.universal_base import UniversalBlock
from app.schemas.cpm import Activity


class ManpowerPlannerBlock(UniversalBlock):
    auto_validate = False
    name = "manpower_planner"
    version = "1.0.0"
    updated_at = "2026-07-19"
    description = "Build a trade-based manpower histogram from CPM results"
    layer = 3
    tags = ["domain", "construction", "schedule", "manpower", "histogram"]
    requires = []

    default_config = {
        "default_period_unit": "week",
    }

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Compute a trade-based manpower histogram.

        Accepts either:
          * ``activities`` + ``results`` (CPM output already computed)
          * ``activities`` only -> the block runs CPM first, then histograms
          * ``task_resources`` (TASKRSRC-shaped list) for real P6 resource loading
        """
        params = params or {}
        data = input_data if isinstance(input_data, dict) else {}

        activities = data.get("activities") or params.get("activities") or []
        results = data.get("results") or params.get("results") or []
        task_resources = (
            data.get("task_resources") or params.get("task_resources") or []
        )
        period_unit = (
            data.get("period_unit")
            or params.get("period_unit")
            or self.config.get("default_period_unit", "week")
        )

        if not activities:
            return {"status": "error", "error": "No activities provided"}

        try:
            from app.lib.pm_computations import compute_cpm, resource_histogram
            from app.schemas.cpm import Activity, CPMInput, CPMResult

            act_objects = [_coerce_activity(a) for a in activities]

            if not results and act_objects:
                cpm_output = compute_cpm(CPMInput(activities=act_objects))
                result_objects = list(cpm_output.results)
            else:
                result_objects = [
                    CPMResult(**r) if isinstance(r, dict) else r for r in results
                ]

            histogram = resource_histogram(
                results=result_objects,
                activities=act_objects,
                period_unit=period_unit,
                task_resources=task_resources or None,
            )
            return {
                "status": "success",
                "period_unit": histogram.period_unit,
                "periods": [p.model_dump() for p in histogram.periods],
                "peak_total": histogram.peak_total,
                "peak_period": histogram.peak_period,
                "by_trade_totals": histogram.by_trade_totals,
                "total_manhours": histogram.total_manhours,
            }
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "error": f"Manpower planning failed: {exc}"}


def _coerce_activity(raw: Any) -> Activity:
    from app.schemas.cpm import Dependency, ResourceAssignment

    if isinstance(raw, Activity):
        return raw
    if not isinstance(raw, dict):
        raw = {"id": str(raw)}

    preds = raw.get("predecessors") or []
    normalized_preds: List[Dependency] = []
    for p in preds:
        if isinstance(p, str):
            normalized_preds.append(Dependency(predecessor_id=p))
        elif isinstance(p, dict):
            normalized_preds.append(Dependency(**p))
        else:
            normalized_preds.append(Dependency(predecessor_id=str(p)))

    resources = raw.get("resources") or []
    normalized_resources: List[ResourceAssignment] = []
    for r in resources:
        if isinstance(r, str):
            normalized_resources.append(ResourceAssignment(trade=r))
        elif isinstance(r, dict):
            normalized_resources.append(ResourceAssignment(**r))
        else:
            normalized_resources.append(ResourceAssignment(trade=str(r)))

    payload = {**raw, "predecessors": normalized_preds, "resources": normalized_resources}
    return Activity(**payload)
