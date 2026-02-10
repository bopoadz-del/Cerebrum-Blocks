from __future__ import annotations

from typing import Dict


def land_metrics(inputs: Dict[str, float]) -> Dict[str, float]:
    modules_count = int(inputs.get("modules_count", 1))
    module_area_m2 = float(inputs.get("module_area_m2", 500.0))
    land_area_m2 = float(inputs.get("land_area_m2", modules_count * module_area_m2))
    land_cost_usd_per_m2 = float(inputs.get("land_cost_usd_per_m2", 0.0))

    land_cost_total = land_area_m2 * land_cost_usd_per_m2

    return {
        "land_area_m2": land_area_m2,
        "land_area_ha": land_area_m2 / 10000.0,
        "land_cost_total": land_cost_total,
    }
