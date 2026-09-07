"""Pin the MEP kit's house-path docs: PROVISIONAL joint filter + armed watcher."""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOUSE = ROOT / "docs" / "MEP_KIT.md"
CANONICAL = ROOT / "block_store" / "kits" / "mep_coordination" / "docs" / "MEP_KIT.md"


def test_house_path_exists_and_points_at_canonical():
    text = HOUSE.read_text(encoding="utf-8")
    assert "block_store/kits/mep_coordination/docs/MEP_KIT.md" in text
    assert CANONICAL.is_file()


@pytest.mark.parametrize("path", [HOUSE, CANONICAL])
def test_provisional_joint_threshold_is_documented(path):
    text = path.read_text(encoding="utf-8")
    assert "PROVISIONAL" in text
    assert "10⁻⁶" in text or "10^-6" in text or "1e-6" in text
    assert "0.0844" in text
    assert "84,000" in text or "84000" in text
    assert "24" in text
    assert "no port" in text.lower()
    assert "re-calibration" in text.lower() or "re-calibrate" in text.lower()
    assert "before any verdict" in text.lower()


def test_canonical_doc_keeps_watcher_armed_and_battery_format():
    text = CANONICAL.read_text(encoding="utf-8")
    assert "armed" in text.lower()
    assert "hard" in text
    assert "clearance" in text
    assert "joints" in text
    assert "resolve_rate" in text or "resolve rate" in text
    assert "escalated" in text
