"""Connector Registry Block — lifecycle management for external integrations.

A neutral registry for connectors built on ``BaseConnector``. Supports
registration, health/status badges, test/sync/run tracking, and discovery.
Domain-specific connectors (ERP, CRM, etc.) extend ``BaseConnector`` and are
registered here without leaking domain assumptions.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.core.universal_base import UniversalBlock


class ConnectorRegistryBlock(UniversalBlock):
    """Register, track, and discover external system connectors."""

    name = "connector_registry"
    version = "1.0.0"
    updated_at = "2026-07-19"
    description = (
        "Connector lifecycle registry: register, test, sync, run, and track "
        "status of external system integrations."
    )
    layer = 2
    tags = ["connector", "integration", "registry", "core"]
    requires = ["memory"]

    default_config = {
        "connector_key_prefix": "connector_registry:connectors",
        "run_key_prefix": "connector_registry:runs",
    }

    ui_schema = {
        "input": {
            "type": "json",
            "placeholder": '{"action": "register", "connector_id": "erp", "name": "ERP"}',
            "multiline": True,
        },
        "output": {"type": "json", "fields": [{"name": "result", "type": "json"}]},
        "params": [
            {
                "name": "action",
                "type": "select",
                "label": "Action",
                "options": [
                    "register",
                    "get",
                    "list",
                    "update_status",
                    "record_run",
                    "list_runs",
                ],
                "default": "list",
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
        action = params.get("action") or data.get("action", "list")

        handlers = {
            "register": self._register,
            "get": self._get,
            "list": self._list,
            "update_status": self._update_status,
            "record_run": self._record_run,
            "list_runs": self._list_runs,
        }
        handler = handlers.get(action)
        if not handler:
            return {"status": "error", "error": f"Unknown action: {action}"}
        return await handler(data, params)

    def _connector_key(self, connector_id: str) -> str:
        prefix = self.config.get("connector_key_prefix", "connector_registry:connectors")
        return f"{prefix}:{connector_id}"

    def _run_key(self, run_id: str) -> str:
        prefix = self.config.get("run_key_prefix", "connector_registry:runs")
        return f"{prefix}:{run_id}"

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

    async def _register(self, data: Dict, params: Dict) -> Dict:
        connector_id = data.get("connector_id") or params.get("connector_id")
        name = data.get("name") or params.get("name")
        if not connector_id or not name:
            return {"status": "error", "error": "connector_id and name are required"}

        connector = {
            "connector_id": connector_id,
            "name": name,
            "description": data.get("description", ""),
            "schema": data.get("schema", {}),
            "status": "registered",
            "registered_at": time.time(),
            "last_tested": None,
            "last_error": None,
        }
        await self._store(self._connector_key(connector_id), connector)
        return {"status": "success", "connector": connector}

    async def _get(self, data: Dict, params: Dict) -> Dict:
        connector_id = data.get("connector_id") or params.get("connector_id")
        if not connector_id:
            return {"status": "error", "error": "connector_id is required"}
        connector = await self._fetch(self._connector_key(connector_id))
        if not connector:
            return {"status": "error", "error": "connector not found"}
        return {"status": "success", "connector": connector}

    async def _list(self, data: Dict, params: Dict) -> Dict:
        prefix = self.config.get("connector_key_prefix", "connector_registry:connectors")
        keys = await self._keys(f"{prefix}:")
        connectors = []
        for key in keys:
            value = await self._fetch(key)
            if value:
                connectors.append(value)
        return {"status": "success", "connectors": connectors, "count": len(connectors)}

    async def _update_status(self, data: Dict, params: Dict) -> Dict:
        connector_id = data.get("connector_id") or params.get("connector_id")
        status = data.get("status") or params.get("status")
        if not connector_id or not status:
            return {"status": "error", "error": "connector_id and status are required"}

        connector = await self._fetch(self._connector_key(connector_id))
        if not connector:
            return {"status": "error", "error": "connector not found"}

        connector["status"] = status
        if "last_tested" in data:
            connector["last_tested"] = data["last_tested"]
        if "last_error" in data:
            connector["last_error"] = data["last_error"]
        await self._store(self._connector_key(connector_id), connector)
        return {"status": "success", "connector": connector}

    async def _record_run(self, data: Dict, params: Dict) -> Dict:
        connector_id = data.get("connector_id") or params.get("connector_id")
        run_type = data.get("run_type") or params.get("run_type", "run")
        if not connector_id:
            return {"status": "error", "error": "connector_id is required"}

        run_id = f"run_{int(time.time())}_{connector_id}"
        run = {
            "run_id": run_id,
            "connector_id": connector_id,
            "run_type": run_type,
            "status": data.get("status", "unknown"),
            "duration_ms": data.get("duration_ms"),
            "records_count": data.get("records_count"),
            "error": data.get("error"),
            "timestamp": time.time(),
        }
        await self._store(self._run_key(run_id), run)
        return {"status": "success", "run": run}

    async def _list_runs(self, data: Dict, params: Dict) -> Dict:
        connector_id = data.get("connector_id") or params.get("connector_id")
        prefix = self.config.get("run_key_prefix", "connector_registry:runs")
        keys = await self._keys(f"{prefix}:")
        runs = []
        for key in keys:
            value = await self._fetch(key)
            if value and (not connector_id or value.get("connector_id") == connector_id):
                runs.append(value)
        return {"status": "success", "runs": runs, "count": len(runs)}
