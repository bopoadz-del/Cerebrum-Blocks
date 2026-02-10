from __future__ import annotations


def land_metrics(
    modules_count: int,
    module_area_m2: float,
    land_cost_usd_per_m2: float = 3.0,
) -> dict:
    """
    Calculate land area and cost for a given number of modules using realistic
    container footprints.

    Args:
        modules_count: number of units (e.g. 1, 4, 12)
        module_area_m2: footprint per unit taken from CONFIGS (m²)
        land_cost_usd_per_m2: cost per square meter of land (default $3)

    Returns a dict with keys:
        land_area_m2: total land area (m²)
        land_area_ha: total land area (ha)
        land_cost_usd: total land cost (USD)
    """
    land_area_m2 = modules_count * module_area_m2
    land_cost_usd = land_area_m2 * land_cost_usd_per_m2
    return {
        "land_area_m2": land_area_m2,
        "land_area_ha": land_area_m2 / 10000.0,
        "land_cost_usd": land_cost_usd,
    }
