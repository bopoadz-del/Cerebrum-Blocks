from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from mssdppg.physics.dp2d import DPParams


def build_power_curve(
    speeds: Iterable[float],
    mode: str,
    aero_params: Dict[str, float],
    sim_params: DPParams,
) -> List[Tuple[float, float]]:
    speeds_list = [float(v) for v in speeds]
    air_density = float(aero_params.get("air_density", 1.225))
    area_m2 = float(aero_params.get("swept_area_m2", 45.0))
    cp = float(aero_params.get("cp", 0.35))
    rated_kw = float(aero_params.get("rated_kw", 250.0))

    curve = []
    for speed in speeds_list:
        if mode == "sim":
            inertia = (sim_params.m_upper_arm + sim_params.m_middle + sim_params.m_lower_arm)
            power_kw = 0.002 * inertia * speed**3
        else:
            power_kw = 0.5 * air_density * area_m2 * cp * speed**3 / 1000.0
        power_kw = min(power_kw, rated_kw)
        curve.append((speed, round(power_kw, 3)))
    return curve
