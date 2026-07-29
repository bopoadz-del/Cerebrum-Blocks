"""Health must report evaluated Kimi workbench capability, not registration."""

import pytest

from app.routers import health as health_router


def test_health_probes_kimi_cli(tmp_path, monkeypatch):
    monkeypatch.setenv("KIMI_CLI_PATH", str(tmp_path / "missing-kimi"))
    body = health_router.health()
    probe = body["kimi_workbench"]
    assert probe["cli_ok"] is False
    assert probe["registered"] is True


def test_health_reports_capability_when_cli_answers(tmp_path, monkeypatch):
    fake = tmp_path / "kimi"
    fake.write_text("#!/bin/sh\necho kimi 1.2.3\nexit 0\n", encoding="utf-8")
    fake.chmod(0o755)
    monkeypatch.setenv("KIMI_CLI_PATH", str(fake))
    body = health_router.health()
    assert body["kimi_workbench"]["cli_ok"] is True
