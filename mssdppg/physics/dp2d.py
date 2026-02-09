from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin
from typing import Dict, List


@dataclass(frozen=True)
class DPParams:
    l1: float
    l2: float
    m_upper_arm: float
    m_middle: float
    m_lower_arm: float
    m_tip: float
    n_pendulums: int


def simulate(wind_speed: float, params: DPParams, duration_s: float = 20.0) -> List[Dict[str, float]]:
    """Return simplified deterministic 2D frames for debugging."""
    steps = max(1, int(duration_s * 10))
    frames: List[Dict[str, float]] = []
    for i in range(steps + 1):
        t = i / 10.0
        phase = (wind_speed / 12.0) * t
        theta = 20.0 * sin(phase)
        arm_extension = params.l1 + params.l2 * 0.5
        x = arm_extension * cos(phase / 2.0)
        y = arm_extension * sin(phase / 2.0)
        kinetic = 0.5 * params.m_tip * (wind_speed ** 2)
        frames.append(
            {
                "t": round(t, 3),
                "theta_deg": round(theta, 3),
                "x": round(x, 3),
                "y": round(y, 3),
                "kinetic_j": round(kinetic, 3),
            }
        )
    return frames
