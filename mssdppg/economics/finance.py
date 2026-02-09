from __future__ import annotations

from typing import Dict


def net_present_value(cashflows: Dict[int, float], discount_rate: float) -> float:
    return sum(amount / ((1 + discount_rate) ** year) for year, amount in cashflows.items())
