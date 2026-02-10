from __future__ import annotations

from math import cos, pi
from typing import Dict, List


def smoothing_curve(
    modules: int = 4,
    phase_offset_deg: float = 30.0,
    inverter_rating_kw: float = 250.0,
    base_power_kw: float = 120.0,
) -> Dict[str, List[float]]:
    clipping_loss_pct = []
    smoothing_index = []
    phase_offset_rad = phase_offset_deg * pi / 180.0
    for step in range(0, 361, 10):
        angle_rad = step * pi / 180.0
        total_kw = 0.0
        for module in range(modules):
            total_kw += base_power_kw * (1 + cos(angle_rad + module * phase_offset_rad)) / 2.0
        clipped_kw = min(total_kw, inverter_rating_kw)
        clipping_loss = max(total_kw - clipped_kw, 0.0)
        clipping_loss_pct.append(round((clipping_loss / max(total_kw, 1e-6)) * 100.0, 3))
        smoothing_index.append(round(clipped_kw / max(inverter_rating_kw, 1e-6), 4))
    return {"clipping_loss_pct": clipping_loss_pct, "smoothing_index": smoothing_index}
