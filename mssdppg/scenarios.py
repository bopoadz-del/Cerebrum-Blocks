from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Scenario:
    name: str
    l1: float
    l2: float
    m_upper_arm: float
    m_middle: float
    m_lower_arm: float
    m_tip: float
    n_pendulums: int
    weibull_k: float
    weibull_c: float


DEFAULT_SCENARIO = Scenario(
    name="baseline",
    l1=1.8,
    l2=2.2,
    m_upper_arm=120.0,
    m_middle=85.0,
    m_lower_arm=60.0,
    m_tip=40.0,
    n_pendulums=3,
    weibull_k=2.0,
    weibull_c=8.0,
)

INVESTOR_SCENARIOS: List[Dict[str, float]] = [
    {
        "name": "Conservative",
        "wacc_pct": 6.5,
        "capex_multiplier": 1.15,
        "land_cost_usd_per_m2": 4.5,
    },
    {
        "name": "Balanced",
        "wacc_pct": 8.0,
        "capex_multiplier": 1.0,
        "land_cost_usd_per_m2": 3.0,
    },
    {
        "name": "Aggressive",
        "wacc_pct": 10.5,
        "capex_multiplier": 0.9,
        "land_cost_usd_per_m2": 1.5,
    },
]


def scenario_dict() -> Dict[str, float]:
    return asdict(DEFAULT_SCENARIO)
