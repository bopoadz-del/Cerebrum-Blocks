"""Tests for domain kit runtime block registration."""

from __future__ import annotations

import pytest

from app.core.domain_kit_loader import _KIT_BLOCK_SPECS


_REAL_DOMAIN_KITS = [
    "agriculture",
    "automotive",
    "aviation",
    "construction",
    "education",
    "finance",
    "hotel_management",
    "hr",
    "insurance",
    "legal",
    "manufacturing",
    "medical",
    "oil_gas",
    "pharma",
    "real_estate",
    "retail",
    "supply_chain",
]


@pytest.mark.parametrize("kit_id", _REAL_DOMAIN_KITS)
def test_real_domain_kit_includes_formula_executor_v2(kit_id: str):
    specs = _KIT_BLOCK_SPECS.get(kit_id, [])
    block_ids = {spec[0] for spec in specs}
    assert "formula_executor_v2" in block_ids, f"{kit_id} missing runtime formula_executor_v2 registration"


@pytest.mark.parametrize("kit_id", _REAL_DOMAIN_KITS)
def test_real_domain_kit_keeps_primary_domain_v2_block(kit_id: str):
    specs = _KIT_BLOCK_SPECS.get(kit_id, [])
    block_ids = {spec[0] for spec in specs}
    expected = f"{kit_id}_v2"
    # hotel_management uses the id "hotel_v2"
    if kit_id == "hotel_management":
        expected = "hotel_v2"
    assert expected in block_ids, f"{kit_id} missing primary {expected} block"


def test_maintenance_placeholder_does_not_include_formula_executor_v2():
    specs = _KIT_BLOCK_SPECS.get("maintenance", [])
    block_ids = {spec[0] for spec in specs}
    assert "formula_executor_v2" not in block_ids
