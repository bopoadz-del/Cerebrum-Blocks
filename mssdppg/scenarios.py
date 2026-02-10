"""
Scenario definitions for validated MSSDPPG configurations.

This module exports a default scenario derived from the rubric-defined
4×40 ft asymmetric system. For other scenarios, import CONFIGS from
mssdppg.configurations and select the desired entry.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from mssdppg.configurations import CONFIGS, calculate_arm_masses


def _build_default() -> Dict[str, Any]:
    base = deepcopy(CONFIGS["4x40ft_asymmetric"])
    m_upper_arm, m_lower_arm = calculate_arm_masses(base["L1"], base["L2"])
    return {
        "name": base["name"],
        "l1": base["L1"],
        "l2": base["L2"],
        "m_upper_arm": m_upper_arm,
        "m_middle": base["m_middle"],
        "m_lower_arm": m_lower_arm,
        "m_tip": base["m_tip"],
        "n_pendulums": base["pendulums"],
        "swept_area_m2": 57.6,
        "cp": 0.35,
        "rho": 1.225,
        "drivetrain_eff": 0.96,
        "availability": 0.97,
        "inverter_rating_kw": 250.0,
        "weibull_k": 2.0,
        "weibull_c": 8.0,
        "expected_power": base["expected_power"],
        "cost": base["cost"],
        "module_area_m2": base["module_area_m2"],
    }


DEFAULT_SCENARIO = _build_default()


def get_default_scenario() -> Dict[str, Any]:
    """Return a deep copy of the default scenario configuration."""
    return deepcopy(DEFAULT_SCENARIO)


INVESTOR_SCENARIOS: List[Dict[str, float]] = [
    {"name": "Conservative", "multiplier": 1.1},
    {"name": "Base", "multiplier": 1.0},
    {"name": "Aggressive", "multiplier": 0.9},
]


def scenario_dict() -> Dict[str, Any]:
    return get_default_scenario()
