"""In-process DATA_DIR backups: run, record, restore, survive.

New-shape tests for the 2026-08-02 finding that no Render cron job can ever
back up this service's disk (cron jobs cannot mount disks; a disk belongs to
one service). The scheduler therefore lives inside the web service. These
tests go all the way round — seed real data, snapshot, restore into a clean
location, compare — because "an archive was produced" is not the property
that matters; "the data comes back" is.
"""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
from datetime import datetime, timezone

import pytest

from app.core import backup as bk
from app.core import backup_scheduler as sched


def _seed_data_dir(root, rows=4):
    root.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(root / "rate_limits.db"))
    try:
        conn.execute("CREATE TABLE usage (key_digest TEXT PRIMARY KEY, hits INTEGER)")
        for i in range(rows):
            conn.execute("INSERT INTO usage VALUES (?,?)", (f"digest_{i}", i * 10))
        conn.commit()
    finally:
        conn.close()
    captures = root / "captures"
    captures.mkdir(exist_ok=True)
    (captures / "shot.txt").write_text("capture payload", encoding="utf-8")
    (root / "publishers.json").write_text('{"publishers": []}', encoding="utf-8")


class TestScheduleArithmetic:
    def test_later_today_when_hour_is_ahead(self):
        now = datetime(2026, 8, 2, 1, 30, tzinfo=timezone.utc)
        assert sched.seconds_until_next_run(4, now) == pytest.approx(150 * 60)

    def test_exactly_on_the_hour_schedules_tomorrow_not_now(self):
        now = datetime(2026, 8, 2, 4, 0, 0, tzinfo=timezone.utc)
        assert sched.seconds_until_next_run(4, now) == pytest.approx(24 * 3600)

    def test_bad_hour_env_falls_back_to_default(self, monkeypatch):
        monkeypatch.setenv(sched.HOUR_ENV, "nope")
        assert sched.scheduled_hour() == sched.DEFAULT_HOUR
        monkeypatch.setenv(sched.HOUR_ENV, "-1")
        assert sched.scheduled_hour() == sched.DEFAULT_HOUR


class TestBackupRoundTrip:
    def test_snapshot_restores_with_identical_rows(self, tmp_path, monkeypatch):
        data = tmp_path / "data"
        monkeypatch.setenv("DATA_DIR", str(data))
        monkeypatch.delenv("BACKUP_DIR", raising=False)
        _seed_data_dir(data)

        result = bk.create_backup()
        assert result.ok, result.error
        assert "rate_limits.db" in result.included
        assert "captures" in result.included
        # The backups directory itself must never be captured (that recurses).
        assert "backups" in result.skipped or "backups" not in result.included

        restored = bk.restore_backup(result.archive, tmp_path / "restore")
        assert restored["verified"]["rate_limits.db"]["usage"] == 4
        assert (
            (tmp_path / "restore" / "captures" / "shot.txt").read_text(
                encoding="utf-8"
            )
            == "capture payload"
        )

    def test_wal_side_files_are_excluded_not_copied(self, tmp_path, monkeypatch):
        """The online snapshot already folds WAL content into the .db; copying
        a live -wal file alongside it would restore a torn state on top of a
        clean one."""
        data = tmp_path / "data"
        monkeypatch.setenv("DATA_DIR", str(data))
        monkeypatch.delenv("BACKUP_DIR", raising=False)
        _seed_data_dir(data)
        (data / "rate_limits.db-wal").write_bytes(b"\x00" * 32)
        (data / "rate_limits.db-shm").write_bytes(b"\x00" * 32)

        result = bk.create_backup()
        assert result.ok, result.error
        restored_dir = tmp_path / "restore"
        bk.restore_backup(result.archive, restored_dir)
        assert not (restored_dir / "rate_limits.db-wal").exists()
        assert not (restored_dir / "rate_limits.db-shm").exists()


class TestRunBackupOnce:
    def test_success_writes_status_and_prunes(self, tmp_path, monkeypatch):
        data = tmp_path / "data"
        monkeypatch.setenv("DATA_DIR", str(data))
        monkeypatch.delenv("BACKUP_DIR", raising=False)
        monkeypatch.setenv(sched.KEEP_ENV, "2")
        _seed_data_dir(data)
        root = bk.backup_root()
        root.mkdir(parents=True, exist_ok=True)
        for stamp in ("20200101T000000Z", "20200102T000000Z", "20200103T000000Z"):
            (root / f"{bk.ARCHIVE_PREFIX}{stamp}.tar.gz").write_bytes(b"stale")

        report = sched.run_backup_once()

        assert report["ok"] is True
        assert os.path.getsize(report["archive"]) > 0
        assert report["pruned"], "retention pruning did not run"
        remaining = list(root.glob(f"{bk.ARCHIVE_PREFIX}*.tar.gz"))
        assert len(remaining) == 2

        status = json.loads(sched.status_path().read_text(encoding="utf-8"))
        assert status["ok"] is True
        assert sched.last_status()["ok"] is True

    def test_failure_is_recorded_not_raised(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
        monkeypatch.delenv("BACKUP_DIR", raising=False)

        def explode(**_kwargs):
            raise RuntimeError("disk on fire")

        monkeypatch.setattr(bk, "create_backup", explode)

        report = sched.run_backup_once()  # must NOT raise

        assert report["ok"] is False
        assert "disk on fire" in report["error"]
        status = json.loads(sched.status_path().read_text(encoding="utf-8"))
        assert status["ok"] is False


class TestArming:
    def test_disabled_flag_arms_nothing(self, monkeypatch):
        monkeypatch.setenv(sched.ENABLED_ENV, "0")

        async def arm():
            return sched.start()

        assert asyncio.run(arm()) is None

    def test_bootstrap_snapshot_taken_when_no_archive_exists(
        self, monkeypatch, tmp_path
    ):
        """A fresh deployment must not wait a day for its first protection."""
        data = tmp_path / "data"
        monkeypatch.setenv("DATA_DIR", str(data))
        monkeypatch.delenv("BACKUP_DIR", raising=False)
        _seed_data_dir(data)
        assert sched.has_any_archive() is False

        ran = asyncio.Event()
        real_run = sched.run_backup_once

        def tracked_run():
            result = real_run()
            ran.set()
            return result

        monkeypatch.setattr(sched, "run_backup_once", tracked_run)

        async def boot():
            task = asyncio.get_running_loop().create_task(sched.scheduler_loop())
            await asyncio.wait_for(ran.wait(), timeout=30)
            task.cancel()

        asyncio.run(boot())
        assert sched.has_any_archive() is True
        assert sched.last_status()["ok"] is True
