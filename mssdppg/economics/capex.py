from __future__ import annotations

from typing import Dict


def total_capex(inputs: Dict[str, float]) -> float:
    base_total = sum(float(value) for value in inputs.values())
    contingency_pct = float(inputs.get("contingency_pct", 0.0))
    return base_total * (1.0 + contingency_pct / 100.0)
