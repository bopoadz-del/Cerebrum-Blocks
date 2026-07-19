"""Agent Catalog Block — declarative agent manifests, hats, and handoffs.

Stores neutral agent definitions that can be composed at runtime: a base agent
plus one or more domain hats, activation triggers, handoff rules, and a
playbook. Inspired by TEKsystem's agent catalog, but with no retail or
fork-specific assumptions.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.core.universal_base import UniversalBlock


class AgentCatalogBlock(UniversalBlock):
    """Declarative catalog for composable agents."""

    name = "agent_catalog"
    version = "1.0.0"
    updated_at = "2026-07-19"
    description = (
        "Declarative agent catalog: manifests, hats, activation triggers, "
        "handoff rules, and memory policies."
    )
    layer = 2
    tags = ["agents", "catalog", "orchestration", "core"]
    requires = ["memory"]

    default_config = {
        "manifest_key_prefix": "agent_catalog:manifests",
    }

    ui_schema = {
        "input": {
            "type": "json",
            "placeholder": '{"action": "create_manifest", "manifest": {...}}',
            "multiline": True,
        },
        "output": {"type": "json", "fields": [{"name": "result", "type": "json"}]},
        "params": [
            {
                "name": "action",
                "type": "select",
                "label": "Action",
                "options": [
                    "create_manifest",
                    "get_manifest",
                    "list_manifests",
                    "validate_manifest",
                    "resolve",
                ],
                "default": "list_manifests",
            }
        ],
        "quick_actions": [],
    }

    def __init__(self, hal_block=None, config: Dict = None):
        super().__init__(hal_block, config)
        self.memory_block = None  # Wired by assembler or tests

    async def _legacy_initialize(self) -> bool:
        return True

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        data = input_data if isinstance(input_data, dict) else {}
        params = params or {}
        action = params.get("action") or data.get("action", "list_manifests")

        handlers = {
            "create_manifest": self._create_manifest,
            "get_manifest": self._get_manifest,
            "list_manifests": self._list_manifests,
            "validate_manifest": self._validate_manifest,
            "resolve": self._resolve,
        }
        handler = handlers.get(action)
        if not handler:
            return {"status": "error", "error": f"Unknown action: {action}"}
        return await handler(data, params)

    def _key(self, manifest_id: str) -> str:
        prefix = self.config.get("manifest_key_prefix", "agent_catalog:manifests")
        return f"{prefix}:{manifest_id}"

    async def _store(self, key: str, value: Dict) -> None:
        if self.memory_block:
            await self.memory_block.process(
                {"action": "set", "key": key, "value": value, "ttl": 0}
            )

    async def _fetch(self, key: str) -> Optional[Dict]:
        if not self.memory_block:
            return None
        result = await self.memory_block.process({"action": "get", "key": key})
        return result.get("value") if result.get("hit") else None

    async def _keys(self, prefix: str) -> List[str]:
        if not self.memory_block:
            return []
        result = await self.memory_block.process({"action": "keys"})
        return [k for k in result.get("keys", []) if k.startswith(prefix)]

    def _validate_manifest(self, data: Dict, params: Dict) -> Dict:
        manifest = data.get("manifest") or params.get("manifest")
        if not isinstance(manifest, dict):
            return {"status": "error", "error": "manifest must be a dict"}
        required = ["manifest_id", "name", "base_agent"]
        missing = [f for f in required if not manifest.get(f)]
        if missing:
            return {"status": "error", "error": f"missing required fields: {', '.join(missing)}"}
        return {"status": "success", "valid": True}

    async def _create_manifest(self, data: Dict, params: Dict) -> Dict:
        manifest = data.get("manifest") or params.get("manifest")
        validation = self._validate_manifest({"manifest": manifest}, {})
        if validation.get("status") == "error":
            return validation

        manifest = dict(manifest)
        manifest.setdefault("hats", [])
        manifest.setdefault("activation_triggers", [])
        manifest.setdefault("handoff_rules", [])
        manifest.setdefault("playbook", {})
        manifest.setdefault("memory_policy", {})
        manifest["created_at"] = time.time()

        await self._store(self._key(manifest["manifest_id"]), manifest)
        return {"status": "success", "manifest": manifest}

    async def _get_manifest(self, data: Dict, params: Dict) -> Dict:
        manifest_id = data.get("manifest_id") or params.get("manifest_id")
        if not manifest_id:
            return {"status": "error", "error": "manifest_id is required"}
        manifest = await self._fetch(self._key(manifest_id))
        if not manifest:
            return {"status": "error", "error": "manifest not found"}
        return {"status": "success", "manifest": manifest}

    async def _list_manifests(self, data: Dict, params: Dict) -> Dict:
        prefix = self.config.get("manifest_key_prefix", "agent_catalog:manifests")
        keys = await self._keys(f"{prefix}:")
        manifests = []
        for key in keys:
            value = await self._fetch(key)
            if value:
                manifests.append(value)
        return {"status": "success", "manifests": manifests, "count": len(manifests)}

    async def _resolve(self, data: Dict, params: Dict) -> Dict:
        """Pick the best manifest given a message/context and triggers."""
        message = (data.get("message") or params.get("message") or "").lower()
        context = data.get("context") or params.get("context") or {}
        prefix = self.config.get("manifest_key_prefix", "agent_catalog:manifests")
        keys = await self._keys(f"{prefix}:")

        best = None
        best_score = 0
        for key in keys:
            manifest = await self._fetch(key)
            if not manifest:
                continue
            score = self._score_manifest(manifest, message, context)
            if score > best_score:
                best_score = score
                best = manifest

        if not best:
            return {"status": "error", "error": "no matching manifest"}
        return {
            "status": "success",
            "manifest_id": best["manifest_id"],
            "name": best["name"],
            "base_agent": best["base_agent"],
            "hats": best.get("hats", []),
            "score": best_score,
        }

    def _score_manifest(self, manifest: Dict, message: str, context: Dict) -> int:
        score = 0
        triggers = manifest.get("activation_triggers", [])
        for trigger in triggers:
            if trigger.lower() in message:
                score += 10
        # Context keys can boost matches
        for key in context.keys():
            if any(key.lower() in t.lower() for t in triggers):
                score += 5
        return score
