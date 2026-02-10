from __future__ import annotations

from typing import Dict


def _capital_recovery_factor(wacc_pct: float, years: int) -> float:
    rate = wacc_pct / 100.0
    if years <= 0:
        return 0.0
    if rate <= 0.0:
        return 1.0 / years
    return rate * (1 + rate) ** years / ((1 + rate) ** years - 1)


def lcoe_table(inputs: Dict[str, float]) -> Dict[str, float]:
    """
    Compute LCOE.

    Supports two input styles:

    1) Legacy breakdown (existing API style):
       - mechanical_usd, electrical_usd, civil_bos_usd, soft_costs_usd, contingency_pct

    2) Rubric/system style (new config-based style):
       - system_cost_usd (total system CAPEX from the validated configuration)

    Shared required/optional:
       - aep_kwh (required)
       - project_life_years (default 20)
       - wacc_pct (default 8.0)
       - fixed_om_usd_per_year (default 0.0)
       - variable_om_usd_per_kwh (default 0.0)
    """
    # Prefer the rubric/system total cost when provided
    if "system_cost_usd" in inputs:
        capex = float(inputs.get("system_cost_usd", 0.0))
    else:
        mechanical = float(inputs.get("mechanical_usd", 0.0))
        electrical = float(inputs.get("electrical_usd", 0.0))
        civil = float(inputs.get("civil_bos_usd", 0.0))
        soft = float(inputs.get("soft_costs_usd", 0.0))
        contingency_pct = float(inputs.get("contingency_pct", 0.0))

        capex = mechanical + electrical + civil + soft
        capex *= 1.0 + contingency_pct / 100.0

    aep_kwh = float(inputs.get("aep_kwh", 0.0))
    life_years = int(inputs.get("project_life_years", 20))
    wacc_pct = float(inputs.get("wacc_pct", 8.0))
    fixed_om = float(inputs.get("fixed_om_usd_per_year", 0.0))
    variable_om = float(inputs.get("variable_om_usd_per_kwh", 0.0))

    annual_om = fixed_om + variable_om * aep_kwh
    crf = _capital_recovery_factor(wacc_pct, life_years)
    annualized_capex = capex * crf

    lcoe = (annualized_capex + annual_om) / aep_kwh if aep_kwh > 0 else 0.0

    return {
        "capex_total_usd": capex,
        "annualized_capex_usd": annualized_capex,
        "annual_om_usd": annual_om,
        "aep_kwh": aep_kwh,
        "lcoe_usd_per_kwh": lcoe,
        "wacc_pct": wacc_pct,
        "project_life_years": life_years,
    }


def lcoe_from_system(
    system_cost_usd: float,
    aep_kwh: float,
    project_life_years: int = 20,
    wacc_pct: float = 8.0,
    fixed_om_usd_per_year: float = 0.0,
    variable_om_usd_per_kwh: float = 0.0,
) -> Dict[str, float]:
    """
    Convenience wrapper for config-based LCOE (rubric system cost + computed AEP).
    """
    return lcoe_table(
        {
            "system_cost_usd": float(system_cost_usd),
            "aep_kwh": float(aep_kwh),
            "project_life_years": int(project_life_years),
            "wacc_pct": float(wacc_pct),
            "fixed_om_usd_per_year": float(fixed_om_usd_per_year),
            "variable_om_usd_per_kwh": float(variable_om_usd_per_kwh),
        }
    )
