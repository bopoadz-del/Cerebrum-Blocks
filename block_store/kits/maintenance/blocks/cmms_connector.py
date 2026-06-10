"""CMMS connector stub — inherits BaseConnector."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx

from app.blocks.core.base_connector import BaseConnector
from app.core.connector_events import ConnectorEvent


class CmmsConnectorBlock(BaseConnector):
    """Stub for Computerized Maintenance Management System integration."""

    name = "cmms_connector"
    version = "0.1.0-skeleton"
    description = "CMMS work order connector (stub)"
    layer = 3
    tags = ["maintenance", "connector", "cmms", "workorder", "stub"]
    connector_source = "cmms"

    default_config = {
        "cmms_base_url": os.getenv("CMMS_BASE_URL", ""),
        "cmms_api_key": os.getenv("CMMS_API_KEY", ""),
        "timeout_seconds": 30,
    }

    ui_schema = {
        "input": {
            "type": "json",
            "placeholder": '{"action": "fetch", "work_order_id": "WO-1001"}',
            "multiline": True,
        },
        "output": {
            "type": "json",
            "fields": [
                {"name": "event", "type": "json", "label": "Connector Event"},
                {"name": "work_orders", "type": "json", "label": "Work Orders"},
            ],
        },
        "params": [
            {"name": "action", "type": "select", "label": "Action", "options": ["fetch", "auth", "health"], "default": "fetch"},
            {"name": "work_order_id", "type": "text", "label": "Work Order ID"},
            {"name": "status", "type": "select", "label": "Status Filter", "options": ["open", "in_progress", "closed", "all"], "default": "open"},
        ],
        "quick_actions": [
            {"icon": "🔧", "label": "Fetch work orders", "prompt": "Fetch CMMS work orders"},
        ],
    }

    def _base_url(self) -> str:
        return (self.config.get("cmms_base_url") or os.getenv("CMMS_BASE_URL", "")).rstrip("/")

    def _api_key(self) -> str:
        return self.config.get("cmms_api_key") or os.getenv("CMMS_API_KEY", "")

    async def authenticate(self) -> Dict[str, Any]:
        base = self._base_url()
        key = self._api_key()
        if not base:
            return {"authenticated": False, "error": "CMMS_BASE_URL not configured"}
        if not key:
            return {"authenticated": False, "error": "CMMS_API_KEY not configured"}
        return {"authenticated": True, "method": "api_key", "base_url": base}

    async def fetch_raw(self, input_data: Any, params: Dict) -> Any:
        data = input_data if isinstance(input_data, dict) else {}
        work_order_id = params.get("work_order_id") or data.get("work_order_id")
        status = params.get("status") or data.get("status", "open")
        base = self._base_url()
        key = self._api_key()

        if not base or not key:
            return {
                "stub": True,
                "work_orders": [
                    {
                        "work_order_id": work_order_id or "WO-STUB-001",
                        "title": "HVAC filter replacement",
                        "status": status if status != "all" else "open",
                        "priority": "medium",
                        "asset_id": "HVAC-LOBBY-1",
                    }
                ],
                "message": "CMMS not configured — returning stub response",
            }

        url = f"{base}/api/v1/work-orders"
        if work_order_id:
            url = f"{base}/api/v1/work-orders/{work_order_id}"
        headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
        query = None if work_order_id else {"status": status} if status != "all" else None
        timeout = float(self.config.get("timeout_seconds", 30))

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, headers=headers, params=query)
            resp.raise_for_status()
            return resp.json()

    def normalize(
        self, raw: Any, params: Optional[Dict] = None, input_data: Any = None
    ) -> ConnectorEvent:
        work_orders = []
        if isinstance(raw, dict):
            if "work_orders" in raw:
                work_orders = raw["work_orders"]
            elif "work_order_id" in raw:
                work_orders = [raw]
            elif isinstance(raw.get("data"), list):
                work_orders = raw["data"]
        return ConnectorEvent(
            source=self.connector_source,
            event_type="cmms.work_orders.fetched",
            payload=raw if isinstance(raw, dict) else {"data": raw},
            normalized_data={
                "count": len(work_orders) if isinstance(work_orders, list) else 0,
                "work_orders": work_orders,
            },
            tags=["maintenance", "cmms", "workorder"],
        )
