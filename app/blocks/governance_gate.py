"""Governance gate block — the Cerebrum-FinanceOps governance service,
neutralized for the Store (in-process tenant-scoped ledger instead of
SQLAlchemy) with the contract preserved: valid action types and risk
tiers, fail-closed ``require_approved`` (an unapproved action is
refused, never silently passed), pending-only approve/reject with a
recorded reviewer, and rejection reasons kept in evidence.

Donor: Cerebrum-FinanceOps backend/app/governance/service.py.
"""

from __future__ import annotations

import itertools
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.universal_base import UniversalBlock

_VALID_ACTION_TYPES = {
    "coa_activation",
    "journal_post",
    "budget_lock",
    "scenario_publish",
    "export_distribution",
}
_VALID_RISK_TIERS = {"low", "medium", "high"}
_VALID_USE_CASE_STATUSES = {"draft", "active", "retired"}
_VALID_VALIDATION_STATUSES = {"pending", "approved", "failed"}

# tenant_id -> ledger
_LEDGERS: Dict[str, Dict[str, Any]] = {}
_ids = itertools.count(1)


def _ledger(tenant_id: str) -> Dict[str, Any]:
    return _LEDGERS.setdefault(
        tenant_id, {"requests": {}, "use_cases": [], "model_records": []}
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_id(prefix: str) -> str:
    return f"{prefix}-{next(_ids)}"


class GovernanceGateBlock(UniversalBlock):
    name = "governance_gate"
    version = "1.0.0"
    description = (
        "Fail-closed approval governance: an action with no approved "
        "request is refused; approve/reject only from pending, with a "
        "recorded reviewer and evidence."
    )
    layer = 1
    tags = ["security", "governance", "approval", "enterprise"]
    requires = []

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        params = params or {}
        data = input_data if isinstance(input_data, dict) else {}
        action = params.get("action", data.get("action", "require_approved"))
        tenant_id = str(params.get("tenant_id", data.get("tenant_id", "local")))
        ledger = _ledger(tenant_id)

        if action == "create_request":
            return self._create_request(ledger, tenant_id, data)
        if action == "list_requests":
            return self._list_requests(ledger, data)
        if action == "get_request":
            return self._get_request(ledger, data)
        if action == "approve_request":
            return self._resolve(ledger, data, "approved")
        if action == "reject_request":
            return self._resolve(ledger, data, "rejected")
        if action == "require_approved":
            return self._require_approved(ledger, tenant_id, data)
        if action == "create_use_case":
            return self._create_use_case(ledger, data)
        if action == "list_use_cases":
            return {
                "status": "success",
                "use_cases": ledger["use_cases"],
            }
        if action == "create_model_governance":
            return self._create_model_governance(ledger, data)
        if action == "list_model_governance":
            return {
                "status": "success",
                "model_records": ledger["model_records"],
            }
        return {"status": "error", "error": f"Unknown action: {action}"}

    # -- approval requests --------------------------------------------------

    def _create_request(self, ledger: Dict, tenant_id: str, data: Dict) -> Dict:
        action_type = data.get("action_type", "")
        if action_type not in _VALID_ACTION_TYPES:
            return {"status": "error", "error": "Invalid action_type"}
        if not data.get("target_id"):
            return {"status": "error", "error": "target_id required"}
        request_id = _next_id("apr")
        record = {
            "id": request_id,
            "tenant_id": tenant_id,
            "project_id": data.get("project_id"),
            "action_type": action_type,
            "target_id": data["target_id"],
            "requester_id": data.get("requester_id"),
            "status": "pending",
            "payload": data.get("payload", {}),
            "evidence": data.get("evidence", {}),
            "reviewer_id": None,
            "created_at": _now(),
            "resolved_at": None,
        }
        ledger["requests"][request_id] = record
        return {"status": "success", "request": dict(record)}

    def _list_requests(self, ledger: Dict, data: Dict) -> Dict:
        out = list(ledger["requests"].values())
        if data.get("status"):
            out = [r for r in out if r["status"] == data["status"]]
        if data.get("project_id"):
            out = [r for r in out if r["project_id"] == data["project_id"]]
        return {
            "status": "success",
            "requests": sorted(out, key=lambda r: r["created_at"], reverse=True),
        }

    def _get_request(self, ledger: Dict, data: Dict) -> Dict:
        record = ledger["requests"].get(data.get("request_id", ""))
        if record is None:
            return {"status": "error", "error": "Approval request not found"}
        return {"status": "success", "request": dict(record)}

    def _resolve(self, ledger: Dict, data: Dict, new_status: str) -> Dict:
        record = ledger["requests"].get(data.get("request_id", ""))
        if record is None:
            return {"status": "error", "error": "Approval request not found"}
        if record["status"] != "pending":
            return {
                "status": "error",
                "error": f"Cannot {'approve' if new_status == 'approved' else 'reject'} "
                f"request in status {record['status']}",
            }
        record["status"] = new_status
        record["reviewer_id"] = data.get("reviewer_id")
        record["resolved_at"] = _now()
        if new_status == "rejected" and data.get("reason"):
            evidence = dict(record["evidence"] or {})
            evidence["rejection_reason"] = data["reason"]
            record["evidence"] = evidence
        return {"status": "success", "request": dict(record)}

    def _require_approved(self, ledger: Dict, tenant_id: str, data: Dict) -> Dict:
        """Fail-closed: the action/target must carry an approved request."""
        action_type = data.get("action_type", "")
        target_id = data.get("target_id", "")
        matches = [
            r
            for r in ledger["requests"].values()
            if r["action_type"] == action_type and r["target_id"] == target_id
        ]
        if not matches:
            return {
                "status": "error",
                "error": "Action requires approved request",
            }
        latest = max(matches, key=lambda r: r["created_at"])
        if latest["status"] != "approved":
            return {
                "status": "error",
                "error": f"Action requires approved request: {latest['id']}",
            }
        return {
            "status": "success",
            "allowed": True,
            "request_id": latest["id"],
            "action_type": action_type,
            "target_id": target_id,
        }

    # -- AI use cases -------------------------------------------------------

    def _create_use_case(self, ledger: Dict, data: Dict) -> Dict:
        risk_tier = data.get("risk_tier", "")
        if risk_tier not in _VALID_RISK_TIERS:
            return {"status": "error", "error": "Invalid risk_tier"}
        status = data.get("status", "draft")
        if status not in _VALID_USE_CASE_STATUSES:
            return {"status": "error", "error": "Invalid status"}
        record = {
            "id": _next_id("uc"),
            "project_id": data.get("project_id"),
            "use_case_name": data.get("use_case_name", ""),
            "description": data.get("description"),
            "model_name": data.get("model_name"),
            "risk_tier": risk_tier,
            "status": status,
            "created_at": _now(),
        }
        ledger["use_cases"].append(record)
        return {"status": "success", "use_case": dict(record)}

    def _create_model_governance(self, ledger: Dict, data: Dict) -> Dict:
        validation_status = data.get("validation_status", "pending")
        if validation_status not in _VALID_VALIDATION_STATUSES:
            return {"status": "error", "error": "Invalid validation_status"}
        record = {
            "id": _next_id("mg"),
            "model_name": data.get("model_name", ""),
            "validation_status": validation_status,
            "notes": data.get("notes"),
            "created_at": _now(),
        }
        ledger["model_records"].append(record)
        return {"status": "success", "model_governance": dict(record)}
