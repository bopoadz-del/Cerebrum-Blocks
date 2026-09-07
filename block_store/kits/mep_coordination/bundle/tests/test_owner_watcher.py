"""The owner-model watcher stays armed and files a battery-format row."""
from __future__ import annotations

import json
from pathlib import Path

from run_owner_models import (
    WATCHER_ARMED,
    file_battery_rows,
    skip_owner_gated,
    verdict_withheld,
)


def test_watcher_is_armed():
    """A disarmed watcher misses the first real IFC. Do not ship that."""
    assert WATCHER_ARMED is True


def test_owner_gated_formats_get_one_log_line_and_skip(tmp_path, capsys):
    for name in ("site.nwd", "federated.nwc", "arch.rvt", "ok.ifc"):
        (tmp_path / name).write_text("x", encoding="utf-8")
    lines = skip_owner_gated(tmp_path)
    assert len(lines) == 3
    assert all(line.startswith("OWNER-GATED:") for line in lines)
    assert "ok.ifc" not in "".join(lines)
    printed = capsys.readouterr().out
    assert printed.count("OWNER-GATED:") == 3


def test_file_battery_rows_writes_level_fields(tmp_path, monkeypatch):
    fake = tmp_path / "owner.ifc"
    fake.write_text("ifc", encoding="utf-8")

    def _row(ifc: Path) -> dict:
        return {
            "model": ifc.name,
            "RECALIBRATION": {"verdict_withheld": False, "band_still_empty": True},
            "zones": [
                {
                    "zone": "L1",
                    "hard": 1,
                    "clearance": 2,
                    "joints_excluded_in_zone": 3,
                    "resolve_rate": 0.5,
                    "escalated": 0,
                }
            ],
        }

    monkeypatch.setattr("run_owner_models.battery_row", _row)
    rows = file_battery_rows([fake], out_dir=tmp_path)
    written = json.loads((tmp_path / "BATTERY_ROWS.json").read_text(encoding="utf-8"))
    assert rows == written
    zone = written[0]["zones"][0]
    for key in ("hard", "clearance", "resolve_rate", "escalated"):
        assert key in zone
    assert "joints_excluded_in_zone" in zone
    assert "RECALIBRATION" in written[0]


def test_verdict_withheld_reads_recalibration_first():
    assert verdict_withheld({"RECALIBRATION": {"verdict_withheld": True}}) is True
    assert verdict_withheld({"RECALIBRATION": {"verdict_withheld": False}}) is False
    assert verdict_withheld({"skipped": True}) is False
