from __future__ import annotations

from typing import Iterable, List, Tuple


def aep_from_bins(curve: Iterable[Tuple[float, float]], bins: List[Tuple[float, float]]) -> float:
    power_by_speed = {float(speed): float(power) for speed, power in curve}
    total_kw = 0.0
    for speed, prob in bins:
        total_kw += power_by_speed.get(float(speed), 0.0) * float(prob)
    return total_kw * 8760.0
