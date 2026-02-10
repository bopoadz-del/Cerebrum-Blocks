from __future__ import annotations


def total_capex(system_cost_usd: float) -> float:
    """
    Return the system cost as provided by the validated configuration.

    The rubric specifies a single total cost for each configuration rather than
    separating mechanical, electrical, civil and soft costs. This helper
    simply returns the passed cost value.
    """
    return float(system_cost_usd)
