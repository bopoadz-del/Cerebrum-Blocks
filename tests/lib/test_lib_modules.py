"""Tests for construction library modules."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.lib import boq_excel, boq_pricing, boq_units, pm_excel, schedule_bridge


def test_boq_units_infer():
    assert boq_units.infer_unit("Concrete slab 200mm") == "m3"
    assert boq_units.infer_unit("Formwork to soffit") == "m2"
    assert boq_units.infer_unit("Reinforcement bar high yield") == "t"
    assert boq_units.infer_unit("PVC pipe 110mm diameter") == "m"


def test_boq_units_canon():
    assert boq_units.canon_unit("sqm") == "m2"
    assert boq_units.canon_unit("cum") == "m3"
    assert boq_units.canon_unit("nos") == "nr"


def test_boq_units_reconcile_blank():
    unit, source, suspect, expected = boq_units.reconcile_unit("", "Concrete footing")
    assert unit == "m3"
    assert source == "inferred"
    assert suspect is False


def test_boq_units_reconcile_suspect():
    unit, source, suspect, expected = boq_units.reconcile_unit("m", "Concrete footing")
    assert unit == "m"
    assert suspect is True
    assert expected == "m3"


def test_boq_pricing_categorize():
    assert boq_pricing.categorize("Concrete slab") == "Concrete"
    assert boq_pricing.categorize("Reinforcement bar") == "Reinforcement"


def test_boq_pricing_price_line_items():
    items = [
        {"description": "Concrete slab", "quantity": 10, "unit": "m3"},
        {"description": "Unknown space widget", "quantity": 5, "unit": "ea"},
    ]
    priced, summary = boq_pricing.price_line_items(items, "construction", "USD")
    assert len(priced) == 2
    assert summary["currency"] == "USD"
    assert summary["exact"] >= 1
    # With an unknown asset, every line is NO RATE.
    priced_unknown, summary_unknown = boq_pricing.price_line_items(
        items, "nonexistent_asset", "USD"
    )
    assert summary_unknown["no_rate"] == 2


def test_schedule_bridge_activity():
    a = schedule_bridge.bridge_activity(
        {"id": "A", "name": "Footing", "duration_days": 5, "resources": ["carpenter"]},
    )
    assert a["duration"] == 5
    assert a["manpower"] == 4  # 1 trade x 4 heads


def test_schedule_bridge_activity_with_day_rate():
    a = schedule_bridge.bridge_activity(
        {"id": "A", "name": "Footing", "duration_days": 5, "resources": ["carpenter"]},
        day_rate=100,
    )
    assert a["cost"] == 2000.0  # 4 * 5 * 100


def test_pm_excel_generate_cost_loaded_schedule():
    activities = [
        {"id": "A", "name": "Start", "duration": 3, "predecessors": [], "manpower": 2, "wbs": "1.1"},
        {"id": "B", "name": "Middle", "duration": 5, "predecessors": ["A"], "manpower": 3, "wbs": "1.2"},
        {"id": "C", "name": "End", "duration": 2, "predecessors": ["B"], "manpower": 1, "wbs": "1.3"},
    ]
    wb = pm_excel.generate_cost_loaded_schedule({"project": "Test"}, activities)
    assert "L2 Schedule" in wb.sheetnames
    assert "Manpower Histogram" in wb.sheetnames


def test_pm_excel_generate_evm_workbook():
    wb = pm_excel.generate_evm_workbook(
        {"project": "Test", "bac": 10000},
        [
            {"period": "W1", "pv": 1000, "ev": 900, "ac": 1100},
            {"period": "W2", "pv": 2000, "ev": 2100, "ac": 1900},
        ],
    )
    assert "EVM" in wb.sheetnames


def test_boq_excel_generate_cost_boq(tmp_path: Path):
    categories = [
        {
            "name": "Concrete",
            "items": [
                {"item_no": "C1", "description": "Footing", "unit": "m3", "qty": 10, "rate": 100},
            ],
        }
    ]
    wb = boq_excel.generate_cost_boq({"project": "Test", "currency": "USD"}, categories)
    path = tmp_path / "boq.xlsx"
    wb.save(str(path))
    total = boq_excel.evaluate_workbook_total(str(path))
    assert total == 1000
