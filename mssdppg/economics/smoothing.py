from __future__ import annotations

from math import cos, pi
from typing import Dict, List


def smoothing_curve(
    modules: int = 4,
    phase_offset_deg: float = 30.0,
    inverter_rating_kw: float = 250.0,
    base_power_kw: float = 120.0,
) -> Dict[str, List[Dict[str, float]]]:
    points = []
    phase_offset_rad = phase_offset_deg * pi / 180.0
    for step in range(0, 361, 10):
        angle_rad = step * pi / 180.0
        total_kw = 0.0
        for module in range(modules):
            total_kw += base_power_kw * (1 + cos(angle_rad + module * phase_offset_rad)) / 2.0
        total_kw = min(total_kw, inverter_rating_kw)
        points.append({"phase_deg": step, "power_kw": round(total_kw, 3)})
    return {"points": points, "modules": modules}
