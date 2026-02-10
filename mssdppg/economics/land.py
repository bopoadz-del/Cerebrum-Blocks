from __future__ import annotations

from typing import Dict


def land_metrics(inputs: Dict[str, float]) -> Dict[str, float]:
    modules_count = int(inputs.get("modules_count", 1))
    module_area_m2 = float(inputs.get("module_area_m2", 500.0))
    spacing_m2 = inputs.get("module_spacing_m2")
    density_per_ha = inputs.get("density_modules_per_ha")
    if spacing_m2:
        land_area_m2 = modules_count * float(spacing_m2)
    elif density_per_ha:
        land_area_m2 = modules_count / (float(density_per_ha) / 10000.0)
    else:
        land_area_m2 = float(inputs.get("land_area_m2", modules_count * module_area_m2))
    land_cost_usd_per_m2 = float(inputs.get("land_cost_usd_per_m2", 0.0))

    land_cost_total = land_area_m2 * land_cost_usd_per_m2

    return {
        "land_area_m2": land_area_m2,
        "land_area_ha": land_area_m2 / 10000.0,
        "land_cost_total": land_cost_total,
    }
