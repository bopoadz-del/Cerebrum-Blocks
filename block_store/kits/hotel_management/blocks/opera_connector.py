"""Oracle Opera PMS connector stub — inherits BaseConnector."""

from __future__ import annotations

from typing import Any, Dict

from app.blocks.core.base_connector import BaseConnector


class OperaConnectorBlock(BaseConnector):
    """Stub for Oracle Opera hotel PMS integration."""

    name = "opera_connector"
    version = "0.1.0-skeleton"
    description = "Oracle Opera PMS connector (stub)"
    layer = 3
    tags = ["hotel", "connector", "opera", "pms", "stub"]
    connector_source = "opera_pms"

    ui_schema = {
        "input": {"type": "json", "placeholder": '{"action": "fetch", "resource": "reservations"}', "multiline": True},
        "output": {"type": "json", "fields": [{"name": "event", "type": "json", "label": "Event"}]},
        "params": [
            {"name": "action", "type": "select", "label": "Action", "options": ["fetch", "auth", "health"], "default": "fetch"},
        ],
        "quick_actions": [],
    }

    async def fetch_raw(self, input_data: Any, params: Dict) -> Any:
        resource = (input_data or {}).get("resource", "reservations") if isinstance(input_data, dict) else "reservations"
        return {
            "stub": True,
            "resource": resource,
            "message": "Opera connector not yet implemented — wire Opera Cloud API",
        }
