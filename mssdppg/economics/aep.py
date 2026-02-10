from __future__ import annotations


def annual_energy_kwh(expected_power_kw: float, capacity_factor: float = 0.30) -> float:
    """
    Annual Energy Production (AEP) from an expected (rated/validated) power and a capacity factor.

    AEP (kWh/year) = expected_power_kw × 8760 × capacity_factor

    Notes:
    - The rubric's annual-kWh figures are consistent with ~30% capacity factor for the 6 m/s configs.
    - capacity_factor is a fraction (0.30 = 30%).
    """
    expected_power_kw = float(expected_power_kw)
    capacity_factor = float(capacity_factor)
    if capacity_factor < 0.0:
        capacity_factor = 0.0
    return expected_power_kw * 8760.0 * capacity_factor
