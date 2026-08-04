"""CI gates and intentional-absence logging.

Two hardening guarantees pinned here:

* The backend CI job actually runs the stub audit and the secret scan —
  both scripts existed but were never wired into the workflow, so their
  gates had never fired on a PR.
* A vector store deliberately deployed without ``DATABASE_URL`` (the
  store service runs no RAG demo flows) logs its absence at INFO, not
  WARNING. Intentional configuration must not read as a fault in the
  boot log.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ci_workflow_runs_stub_audit_and_secret_scan():
    workflow = (_REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "python scripts/audit_stubs.py" in workflow, (
        "CI must run the stub audit (implement-or-register gate)"
    )
    assert "python scripts/scan_secrets.py" in workflow, (
        "CI must run the secret scan on non-test paths"
    )


@pytest.mark.asyncio
async def test_missing_database_url_logs_info_not_warning(monkeypatch, caplog):
    from app.core import vector_store

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(vector_store, "_pool", None)

    with caplog.at_level(logging.INFO, logger="app.core.vector_store"):
        pool = await vector_store.init_pool()

    assert pool is None
    records = [r for r in caplog.records if "DATABASE_URL" in r.getMessage()]
    assert records, "init_pool must still announce the intentional absence"
    assert all(r.levelno == logging.INFO for r in records), (
        "intentional no-DATABASE_URL configuration must log at INFO, "
        f"got: {[(r.levelname, r.getMessage()) for r in records]}"
    )
    assert "expected" in records[0].getMessage()
