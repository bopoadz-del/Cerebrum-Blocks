"""Behavior tests for the governance_gate block (FinanceOps port).

Every assertion exercises the fail-closed contract: no fabricated
approvals, pending-only resolution, reviewer recorded, rejection reason
kept in evidence.
"""

from __future__ import annotations

import pytest

from app.blocks.governance_gate import GovernanceGateBlock, _ledger, _LEDGERS


@pytest.fixture()
def gate():
    return GovernanceGateBlock()


@pytest.fixture(autouse=True)
def _fresh_ledger():
    _LEDGERS.clear()
    yield
    _LEDGERS.clear()


async def _call(gate, action, tenant="t1", **data):
    envelope = await gate.execute({**data, "tenant_id": tenant}, {"action": action})
    return envelope["result"]


@pytest.mark.asyncio
async def test_require_approved_refuses_without_request(gate):
    result = await _call(gate, "require_approved", action_type="budget_lock", target_id="b-1")
    assert result["status"] == "error"
    assert "requires approved request" in result["error"]


@pytest.mark.asyncio
async def test_full_approval_flow_allows_then_rejects_resolution(gate):
    created = await _call(
        gate, "create_request",
        action_type="budget_lock", target_id="b-1",
        requester_id="u1", payload={"amount": 100},
    )
    assert created["status"] == "success"
    request_id = created["request"]["id"]
    assert created["request"]["status"] == "pending"

    # Unapproved -> refused.
    refused = await _call(gate, "require_approved", action_type="budget_lock", target_id="b-1")
    assert refused["status"] == "error"

    # Approve from pending.
    approved = await _call(gate, "approve_request", request_id=request_id, reviewer_id="r1")
    assert approved["status"] == "success"
    assert approved["request"]["status"] == "approved"
    assert approved["request"]["reviewer_id"] == "r1"

    # Now allowed.
    allowed = await _call(gate, "require_approved", action_type="budget_lock", target_id="b-1")
    assert allowed["status"] == "success"
    assert allowed["allowed"] is True
    assert allowed["request_id"] == request_id

    # Double-approve refused.
    again = await _call(gate, "approve_request", request_id=request_id, reviewer_id="r2")
    assert again["status"] == "error"
    assert "status approved" in again["error"]


@pytest.mark.asyncio
async def test_rejection_keeps_reason_and_never_allows(gate):
    created = await _call(
        gate, "create_request",
        action_type="journal_post", target_id="j-9", requester_id="u1",
    )
    request_id = created["request"]["id"]
    rejected = await _call(
        gate, "reject_request", request_id=request_id, reviewer_id="r1", reason="no budget"
    )
    assert rejected["status"] == "success"
    assert rejected["request"]["status"] == "rejected"
    assert rejected["request"]["evidence"]["rejection_reason"] == "no budget"

    refused = await _call(gate, "require_approved", action_type="journal_post", target_id="j-9")
    assert refused["status"] == "error"


@pytest.mark.asyncio
async def test_invalid_action_type_and_risk_tier_are_named(gate):
    bad_type = await _call(
        gate, "create_request", action_type="delete_everything", target_id="x"
    )
    assert bad_type["status"] == "error"
    assert "Invalid action_type" in bad_type["error"]

    bad_risk = await _call(gate, "create_use_case", risk_tier="apocalyptic", use_case_name="x")
    assert bad_risk["status"] == "error"
    assert "Invalid risk_tier" in bad_risk["error"]


@pytest.mark.asyncio
async def test_tenants_are_isolated(gate):
    await _call(gate, "create_request", tenant="t1", action_type="budget_lock", target_id="b-1")
    # Tenant t2 asking about t1's target sees nothing.
    refused = await _call(gate, "require_approved", tenant="t2", action_type="budget_lock", target_id="b-1")
    assert refused["status"] == "error"
    listed = await _call(gate, "list_requests", tenant="t2")
    assert listed["requests"] == []
