"""validate_transition must be reachable as a live block action."""

import pytest

from app.blocks.construction_advisor import ConstructionAdvisorBlock


@pytest.mark.asyncio
async def test_validate_transition_action_allows_legal_transition():
    block = ConstructionAdvisorBlock()
    result = await block.execute(
        {
            "rule_id": "procurement.tender_lifecycle",
            "state": "draft",
            "event": {"to": "issued"},
            "context": {},
        },
        {"action": "validate_transition"},
    )
    body = result["result"]
    assert body["status"] == "success", body
    assert "allowed" in body


@pytest.mark.asyncio
async def test_validate_transition_action_rejects_unknown_rule():
    block = ConstructionAdvisorBlock()
    result = await block.execute(
        {
            "rule_id": "no.such.rule",
            "state": "draft",
            "event": {"to": "issued"},
            "context": {},
        },
        {"action": "validate_transition"},
    )
    body = result["result"]
    assert body["status"] == "error"
