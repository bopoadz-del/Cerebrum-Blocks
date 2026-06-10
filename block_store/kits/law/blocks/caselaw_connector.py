"""Caselaw API connector stub — inherits BaseConnector."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx

from app.blocks.core.base_connector import BaseConnector
from app.core.connector_events import ConnectorEvent


class CaselawConnectorBlock(BaseConnector):
    """Stub for caselaw / legal research API integration."""

    name = "caselaw_connector"
    version = "0.1.0-skeleton"
    description = "Caselaw API search connector (stub)"
    layer = 3
    tags = ["law", "connector", "caselaw", "research", "stub"]
    connector_source = "caselaw_api"

    default_config = {
        "caselaw_api_key": os.getenv("CASELAW_API_KEY", ""),
        "caselaw_base_url": os.getenv("CASELAW_BASE_URL", "https://api.caselaw.example.com"),
        "timeout_seconds": 30,
    }

    ui_schema = {
        "input": {
            "type": "json",
            "placeholder": '{"query": "negligence standard of care", "jurisdiction": "federal"}',
            "multiline": True,
        },
        "output": {
            "type": "json",
            "fields": [
                {"name": "event", "type": "json", "label": "Connector Event"},
                {"name": "cases", "type": "json", "label": "Cases"},
            ],
        },
        "params": [
            {"name": "action", "type": "select", "label": "Action", "options": ["fetch", "auth", "health"], "default": "fetch"},
            {"name": "query", "type": "text", "label": "Search Query"},
            {"name": "jurisdiction", "type": "text", "label": "Jurisdiction"},
            {"name": "limit", "type": "number", "label": "Max results", "default": 10},
        ],
        "quick_actions": [
            {"icon": "📚", "label": "Search caselaw", "prompt": "Search caselaw by legal query"},
        ],
    }

    def _base_url(self) -> str:
        return (
            self.config.get("caselaw_base_url")
            or os.getenv("CASELAW_BASE_URL", "https://api.caselaw.example.com")
        ).rstrip("/")

    def _api_key(self) -> str:
        return self.config.get("caselaw_api_key") or os.getenv("CASELAW_API_KEY", "")

    async def authenticate(self) -> Dict[str, Any]:
        key = self._api_key()
        if not key:
            return {"authenticated": False, "error": "CASELAW_API_KEY not configured"}
        return {"authenticated": True, "method": "api_key", "base_url": self._base_url()}

    async def fetch_raw(self, input_data: Any, params: Dict) -> Any:
        data = input_data if isinstance(input_data, dict) else {}
        query = params.get("query") or data.get("query")
        if not query:
            raise ValueError("query is required for caselaw search")

        jurisdiction = params.get("jurisdiction") or data.get("jurisdiction", "federal")
        limit = int(params.get("limit") or data.get("limit", 10))
        base = self._base_url()
        key = self._api_key()
        url = f"{base}/v1/search"
        headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
        timeout = float(self.config.get("timeout_seconds", 30))

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(
                url,
                headers=headers,
                params={"q": query, "jurisdiction": jurisdiction, "limit": limit},
            )
            if resp.status_code in (401, 404):
                return {
                    "stub": True,
                    "query": query,
                    "jurisdiction": jurisdiction,
                    "cases": [
                        {
                            "case_id": "stub-1",
                            "title": f"Stub result for: {query}",
                            "court": jurisdiction,
                            "citation": "Stub v. Example, 000 U.S. 000 (2024)",
                        }
                    ],
                    "message": "Caselaw API not configured — returning stub response",
                }
            resp.raise_for_status()
            return resp.json()

    def normalize(
        self, raw: Any, params: Optional[Dict] = None, input_data: Any = None
    ) -> ConnectorEvent:
        data = input_data if isinstance(input_data, dict) else {}
        query = (params or {}).get("query") or data.get("query", "")
        cases: List[Any] = []
        if isinstance(raw, dict):
            cases = raw.get("cases") or raw.get("results") or []
        return ConnectorEvent(
            source=self.connector_source,
            event_type="caselaw.search.completed",
            payload=raw if isinstance(raw, dict) else {"data": raw},
            normalized_data={
                "query": query,
                "count": len(cases) if isinstance(cases, list) else 0,
                "cases": cases,
            },
            tags=["law", "caselaw", "research"],
        )
