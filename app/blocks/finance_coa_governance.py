"""Chart of Accounts and dimension-mapping governance block."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from app.core.finance_ops import parse_date, stable_digest
from app.core.typed_block import TypedBlock


class FinanceCoAGovernanceBlock(TypedBlock):
    """Validate future-state CoA hierarchies and effective-dated mappings."""

    name = "finance_coa_governance"
    version = "1.0.0"
    description = (
        "Chart of Accounts governance with hierarchy validation, old-to-new "
        "mapping controls, effective dating, dependency impact analysis, and "
        "deterministic approved-mapping resolution."
    )
    layer = 3
    tags = ["domain", "finance_ops", "chart_of_accounts", "master_data", "governance"]
    requires: List[str] = []
    input_schema = {
        "type": "object",
        "properties": {
            "operation": {"type": "string"},
            "current_accounts": {"type": "array"},
            "proposed_accounts": {"type": "array"},
            "mappings": {"type": "array"},
        },
    }
    output_schema = {
        "type": "object",
        "properties": {"status": {"type": "string"}},
        "required": ["status"],
    }
    accepted_input_types = ["JSON"]
    produced_output_types = ["FinanceCoAGovernanceResult"]
    ui_schema = {
        "input": {"type": "json", "multiline": True},
        "output": {"type": "json"},
        "quick_actions": [
            {"icon": "", "label": "Validate CoA", "prompt": "Validate a proposed Chart of Accounts"},
            {"icon": "", "label": "Impact Analysis", "prompt": "Show reports and models affected by CoA changes"},
        ],
    }

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        data = {**(params or {}), **(input_data if isinstance(input_data, dict) else {})}
        operation = data.get("operation") or "validate"
        try:
            if operation == "validate":
                return self._validate(data)
            if operation == "impact_analysis":
                return self._impact_analysis(data)
            if operation == "resolve_mapping":
                return self._resolve_mapping(data)
        except (TypeError, ValueError) as exc:
            return {"status": "validation_error", "operation": operation, "error": str(exc)}
        return {
            "status": "unsupported",
            "operation": operation,
            "error": f"Unknown operation: {operation}",
            "available_operations": ["validate", "impact_analysis", "resolve_mapping"],
        }

    @staticmethod
    def _account_map(rows: Any, label: str) -> Dict[str, Dict[str, Any]]:
        if rows is None:
            return {}
        if not isinstance(rows, list):
            raise ValueError(f"{label} must be an array")
        result: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError(f"{label} entries must be objects")
            account_id = str(row.get("account_id") or row.get("id") or "").strip()
            if not account_id:
                raise ValueError(f"{label} account_id is required")
            if account_id in result:
                raise ValueError(f"{label} has duplicate account_id '{account_id}'")
            result[account_id] = {**row, "account_id": account_id}
        return result

    def _validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        current = self._account_map(data.get("current_accounts"), "current_accounts")
        proposed = self._account_map(data.get("proposed_accounts"), "proposed_accounts")
        mappings = data.get("mappings") or []
        if not isinstance(mappings, list):
            raise ValueError("mappings must be an array")
        issues = self._hierarchy_issues(proposed) + self._mapping_issues(current, proposed, mappings)
        mapped_sources = {
            str(row.get("old_account_id") or "").strip()
            for row in mappings
            if isinstance(row, dict) and row.get("status", "proposed") != "rejected"
        }
        for account_id, account in current.items():
            if account.get("active", True) and account_id not in mapped_sources:
                issues.append({
                    "severity": "warning", "code": "active_account_unmapped",
                    "account_id": account_id,
                    "message": "Active current account has no proposed mapping",
                })
        blocking = sum(issue["severity"] in {"critical", "error"} for issue in issues)
        payload = {
            "current_account_count": len(current),
            "proposed_account_count": len(proposed),
            "mapping_count": len(mappings),
            "issues": issues,
        }
        return {
            "status": "success" if not blocking else "validation_error",
            "operation": "validate", "valid": not blocking, **payload,
            "evidence_digest": stable_digest(payload),
            "decision_policy": "advisory_only_changes_require_human_approval",
        }

    @staticmethod
    def _hierarchy_issues(accounts: Mapping[str, Mapping[str, Any]]) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        for account_id, account in accounts.items():
            parent = str(account.get("parent_id") or "").strip()
            if parent and parent not in accounts:
                issues.append({
                    "severity": "error", "code": "parent_account_missing",
                    "account_id": account_id, "parent_id": parent,
                    "message": "Parent account does not exist in proposed CoA",
                })
        visiting: Set[str] = set()
        visited: Set[str] = set()

        def visit(account_id: str, trail: List[str]) -> None:
            if account_id in visiting:
                start = trail.index(account_id) if account_id in trail else 0
                issues.append({
                    "severity": "critical", "code": "account_hierarchy_cycle",
                    "cycle": trail[start:] + [account_id],
                    "message": "Proposed CoA contains a parent-child cycle",
                })
                return
            if account_id in visited:
                return
            visiting.add(account_id)
            parent = str(accounts[account_id].get("parent_id") or "").strip()
            if parent in accounts:
                visit(parent, trail + [account_id])
            visiting.discard(account_id)
            visited.add(account_id)

        for account_id in accounts:
            visit(account_id, [])
        return issues

    @staticmethod
    def _mapping_issues(
        current: Mapping[str, Mapping[str, Any]],
        proposed: Mapping[str, Mapping[str, Any]],
        mappings: Sequence[Any],
    ) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        by_source: Dict[str, List[Tuple[Optional[date], Optional[date], int]]] = defaultdict(list)
        for index, mapping in enumerate(mappings, start=1):
            if not isinstance(mapping, dict):
                issues.append({"severity": "error", "code": "mapping_not_object", "mapping_number": index})
                continue
            source = str(mapping.get("old_account_id") or "").strip()
            target = str(mapping.get("new_account_id") or "").strip()
            if source not in current:
                issues.append({"severity": "error", "code": "mapping_source_missing", "mapping_number": index, "old_account_id": source})
            if target not in proposed:
                issues.append({"severity": "error", "code": "mapping_target_missing", "mapping_number": index, "new_account_id": target})
            elif proposed[target].get("active", True) is False:
                issues.append({"severity": "warning", "code": "mapping_target_inactive", "mapping_number": index, "new_account_id": target})
            try:
                start = parse_date(mapping["effective_from"], "effective_from") if mapping.get("effective_from") else None
                end = parse_date(mapping["effective_to"], "effective_to") if mapping.get("effective_to") else None
                if start and end and end < start:
                    issues.append({"severity": "error", "code": "invalid_effective_range", "mapping_number": index})
                by_source[source].append((start, end, index))
            except ValueError as exc:
                issues.append({"severity": "error", "code": "invalid_mapping_date", "mapping_number": index, "message": str(exc)})
            if mapping.get("status", "proposed") == "approved" and not mapping.get("approved_by"):
                issues.append({"severity": "error", "code": "approved_mapping_missing_approver", "mapping_number": index})
        for source, ranges in by_source.items():
            for left_index, left in enumerate(ranges):
                for right in ranges[left_index + 1:]:
                    left_start, left_end, left_number = left
                    right_start, right_end, right_number = right
                    low_left, high_left = left_start or date.min, left_end or date.max
                    low_right, high_right = right_start or date.min, right_end or date.max
                    if max(low_left, low_right) <= min(high_left, high_right):
                        issues.append({
                            "severity": "error", "code": "overlapping_mappings",
                            "old_account_id": source,
                            "mapping_numbers": [left_number, right_number],
                        })
        return issues

    @staticmethod
    def _impact_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
        changed = {str(value) for value in (data.get("changed_account_ids") or [])}
        dependencies = data.get("dependencies") or []
        if not isinstance(dependencies, list):
            raise ValueError("dependencies must be an array")
        impacted = []
        for dependency in dependencies:
            if not isinstance(dependency, dict):
                continue
            refs = {str(value) for value in (dependency.get("account_ids") or [])}
            hits = sorted(changed & refs)
            if hits:
                impacted.append({**dependency, "impacted_account_ids": hits})
        payload = {
            "changed_account_ids": sorted(changed),
            "impacted_dependencies": impacted,
            "impact_count": len(impacted),
        }
        return {
            "status": "success", "operation": "impact_analysis", **payload,
            "evidence_digest": stable_digest(payload),
            "decision_policy": "impact_requires_owner_review_before_release",
        }

    @staticmethod
    def _resolve_mapping(data: Dict[str, Any]) -> Dict[str, Any]:
        account_id = str(data.get("old_account_id") or "").strip()
        if not account_id:
            raise ValueError("old_account_id is required")
        as_of = parse_date(data.get("as_of") or date.today().isoformat(), "as_of")
        candidates = []
        for mapping in data.get("mappings") or []:
            if not isinstance(mapping, dict) or str(mapping.get("old_account_id") or "") != account_id:
                continue
            if mapping.get("status") != "approved":
                continue
            start = parse_date(mapping["effective_from"], "effective_from") if mapping.get("effective_from") else date.min
            end = parse_date(mapping["effective_to"], "effective_to") if mapping.get("effective_to") else date.max
            if start <= as_of <= end:
                candidates.append(mapping)
        if len(candidates) != 1:
            return {
                "status": "dependency_required",
                "operation": "resolve_mapping",
                "old_account_id": account_id,
                "as_of": as_of.isoformat(),
                "candidate_count": len(candidates),
                "error": "Exactly one approved effective mapping is required",
            }
        mapping = candidates[0]
        payload = {
            "old_account_id": account_id,
            "new_account_id": mapping.get("new_account_id"),
            "as_of": as_of.isoformat(),
            "mapping_version": mapping.get("version"),
            "approved_by": mapping.get("approved_by"),
        }
        return {"status": "success", "operation": "resolve_mapping", **payload, "evidence_digest": stable_digest(payload)}
