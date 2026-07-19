"""Tests for app.lib.boq_units."""

import pytest

from app.lib.boq_units import canon_unit, infer_unit, reconcile_unit


@pytest.mark.parametrize(
    "description,expected",
    [
        ("Excavation for foundations", "m3"),
        ("Supply and install 200mm dia PVC pipe", "m"),
        ("Formwork to concrete walls", "m2"),
        ("Reinforcement high yield steel bar", "t"),
        ("Supply and fix ceramic wall tiling", "m2"),
        ("Preliminaries and mobilization", "sum"),
        ("Random unrelated text without rules", None),
    ],
)
def test_infer_unit(description, expected):
    assert infer_unit(description) == expected


@pytest.mark.parametrize(
    "unit,expected",
    [
        ("mq", "m2"),
        ("sqm", "m2"),
        ("cum", "m3"),
        ("nos", "nr"),
        ("EA", "nr"),
        ("LS", "sum"),
        ("m", "m"),
    ],
)
def test_canon_unit(unit, expected):
    assert canon_unit(unit) == expected


@pytest.mark.parametrize(
    "parsed,description,expected_unit,expected_source,expected_suspect,expected_expected",
    [
        ("", "Excavation for foundations", "m3", "inferred", False, None),
        ("m3", "Excavation for foundations", "m3", "parsed", False, None),
        ("m", "Excavation for foundations", "m", "parsed", True, "m3"),
        ("ea", "Supply and install door", "ea", "parsed", False, None),
    ],
)
def test_reconcile_unit(parsed, description, expected_unit, expected_source, expected_suspect, expected_expected):
    unit, source, suspect, expected = reconcile_unit(parsed, description)
    assert unit == expected_unit
    assert source == expected_source
    assert suspect is expected_suspect
    assert expected == expected_expected
