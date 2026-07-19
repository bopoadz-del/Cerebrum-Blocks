"""Tests for app.lib.schedule_bridge."""

from app.lib.schedule_bridge import (
    bridge_activity,
    bridge_assumptions,
    bridge_wbs_to_cost_loaded,
)


def test_bridge_activity_fills_missing_fields():
    raw = {
        "id": "A1",
        "name": "Excavation",
        "duration_days": 10,
        "wbs_phase": "Earthworks",
        "resources": ["Labor", "Operator"],
    }
    out = bridge_activity(raw)
    assert out["id"] == "A1"
    assert out["name"] == "Excavation"
    assert out["wbs"] == "Earthworks"
    assert out["duration"] == 10
    assert out["manpower"] == 8  # 2 trades * 4 default crew/trade
    assert "cost" not in out


def test_bridge_activity_preserves_existing_cost():
    raw = {"id": "A2", "name": "Concrete", "duration": 5, "manpower": 3, "cost": 1000}
    out = bridge_activity(raw)
    assert out["duration"] == 5
    assert out["manpower"] == 3
    assert out["cost"] == 1000.0


def test_bridge_activity_with_day_rate():
    raw = {"id": "A3", "name": "Formwork", "duration_days": 4, "resources": ["Carpenter"]}
    out = bridge_activity(raw, day_rate=50.0)
    assert out["manpower"] == 4
    assert out["cost"] == 4 * 4 * 50.0


def test_bridge_wbs_to_cost_loaded():
    activities = [
        {"id": 1, "name": "a", "duration_days": 2, "resources": ["x"]},
        {"id": 2, "name": "b", "duration_days": 3, "resources": ["y", "z"]},
    ]
    out = bridge_wbs_to_cost_loaded(activities)
    assert len(out) == 2
    assert out[0]["manpower"] == 4
    assert out[1]["manpower"] == 8


def test_bridge_assumptions():
    ass = bridge_assumptions(crew_per_trade=3, day_rate=100.0)
    assert any("3 heads/trade" in a for a in ass)
    assert any("man-days" in a for a in ass)
    assert any("100" in a for a in ass)
