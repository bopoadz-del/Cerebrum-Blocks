"""End-to-end demo flows — the stranger, encoded.

Boots the real app (TestClient) and asserts user-visible outcomes for the
documented Quick-Start flows. Infra-heavy flows (RAG over pgvector) gate on
DATABASE_URL exactly like the rest of the suite; everything else runs cold.

  B2  health 200
  B4  register a block, invoke it, get a typed result
  B5  tenant isolation (covered in depth by tests/core/test_two_tenant_isolation)
  B3  ingest -> RAG query -> cited answer   (needs DATABASE_URL)
"""

from __future__ import annotations

import os
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


def _client() -> TestClient:
    return TestClient(app, headers={"Authorization": "Bearer cb_dev_key"})


# ── B2: health ──────────────────────────────────────────────────────────────
def test_b2_health_and_readiness():
    with TestClient(app) as c:  # health is unauthenticated
        h = c.get("/health")
        assert h.status_code == 200
        assert h.json().get("status") == "ok"
        r = c.get("/ready")
        assert r.status_code in (200, 503)  # 503 only if a real dependency is down
        assert "status" in r.json()


# ── B4: register a block, invoke it, typed result ───────────────────────────
def test_b4_block_is_registered_and_invocable():
    with _client() as c:
        # The block registry is populated at boot; `validation` is a pure,
        # infra-free block. Invoke it and assert a typed (dict) result.
        resp = c.post(
            "/execute",
            json={
                "block": "validation",
                "input": {"action": "validate_pipeline", "item": {"x": 1}},
                "params": {"action": "validate_pipeline"},
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert isinstance(body, dict)
        # A typed result, not an error shrug.
        assert "error" not in body or body.get("error") is None


# ── B5: tenant isolation (smoke; depth in test_two_tenant_isolation) ────────
def test_b5_unauthenticated_execute_is_rejected():
    with TestClient(app) as c:  # no Authorization header
        resp = c.post("/execute", json={"block": "validation", "input": {}})
        assert resp.status_code in (401, 403), resp.text


# ── B6: construction container primary extraction (document -> structured) ──
@pytest.mark.asyncio
async def test_b6_construction_document_extraction(tmp_path):
    from app.containers.construction import ConstructionContainer

    doc = tmp_path / "contract.txt"
    doc.write_text(
        "CONTRACT AGREEMENT\n"
        "The Contractor shall supply and install 1200 m3 of C40 concrete and "
        "85000 kg of reinforcement. The Contract Sum is AED 12,500,000. "
        "Practical Completion within 540 days. Retention shall be 10%.",
        encoding="utf-8",
    )
    container = ConstructionContainer()
    out = await container.route("process_document", {"file_path": str(doc)}, {})
    assert out.get("status") == "success", out
    # The container auto-classifies and routes (drawing / contract / spec / ...);
    # whichever path runs must return a real structured envelope, not a shrug.
    assert out.get("file_name") == "contract.txt"
    classified = out.get("doc_type") or out.get("action") or out.get("contract_type")
    assert classified, f"document was not classified/processed: {out}"
    assert len(out.keys()) > 4, f"extraction envelope too thin: {list(out.keys())}"


# ── B3: ingest -> RAG query -> cited answer (needs pgvector) ────────────────
@pytest.mark.skipif(
    os.getenv("DATABASE_URL") is None,
    reason="DATABASE_URL not set; RAG e2e needs pgvector (provided in CI)",
)
def test_b3_ingest_then_cited_answer():
    tenant = f"e2e-{uuid.uuid4().hex[:8]}"
    fact = "The service level agreement guarantees 99.95% monthly uptime."
    with _client() as c:
        ing = c.post(
            "/ingestion/text",
            json={"tenant_id": tenant, "project_name": "e2e", "title": "SLA", "text": fact},
        )
        assert ing.status_code == 200, ing.text
        project_id = ing.json()["project_id"]
        ask = c.post(
            "/knowledge/ask",
            json={"question": "What uptime does the SLA guarantee?", "project_id": project_id, "top_k": 3},
        )
        assert ask.status_code == 200, ask.text
        ans = ask.json()
    assert ans["status"] == "success"
    assert "99.95" in ans["answer"]
    assert ans.get("chunks_retrieved", 0) >= 1
