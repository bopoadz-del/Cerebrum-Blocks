"""PACER court records connector stub — inherits BaseConnector."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx

from app.blocks.core.base_connector import BaseConnector
from app.core.connector_events import ConnectorEvent


class PacerConnectorBlock(BaseConnector):
    """Stub for PACER (Public Access to Court Electronic Records) integration."""

    name = "pacer_connector"
    version = "0.1.0-skeleton"
    description = "PACER court records search connector (stub)"
    layer = 3
    tags = ["law", "connector", "pacer", "court", "stub"]
    connector_source = "pacer"

    default_config = {
        "pacer_username": os.getenv("PACER_USERNAME", ""),
        "pacer_password": os.getenv("PACER_PASSWORD", ""),
        "pacer_base_url": os.getenv("PACER_BASE_URL", "https://pcl.uscourts.gov"),
        "timeout_seconds": 30,
    }

    ui_schema = {
        "input": {
            "type": "json",
            "placeholder": '{"action": "fetch", "case_number": "1:24-cv-00123"}',
            "multiline": True,
        },
        "output": {
            "type": "json",
            "fields": [
                {"name": "event", "type": "json", "label": "Connector Event"},
                {"name": "filings", "type": "json", "label": "Court Filings"},
            ],
        },
        "params": [
            {"name": "action", "type": "select", "label": "Action", "options": ["fetch", "auth", "health"], "default": "fetch"},
            {"name": "case_number", "type": "text", "label": "Case Number"},
            {"name": "court_id", "type": "text", "label": "Court ID"},
        ],
        "quick_actions": [
            {"icon": "⚖️", "label": "Search PACER", "prompt": "Search PACER court records by case number"},
        ],
    }

    def _base_url(self) -> str:
        return (
            self.config.get("pacer_base_url")
            or os.getenv("PACER_BASE_URL", "https://pcl.uscourts.gov")
        ).rstrip("/")

    def _credentials(self) -> tuple[str, str]:
        user = self.config.get("pacer_username") or os.getenv("PACER_USERNAME", "")
        password = self.config.get("pacer_password") or os.getenv("PACER_PASSWORD", "")
        return user, password

    async def authenticate(self) -> Dict[str, Any]:
        user, password = self._credentials()
        base = self._base_url()
        if not user or not password:
            return {"authenticated": False, "error": "PACER_USERNAME and PACER_PASSWORD required"}
        return {"authenticated": True, "method": "basic", "base_url": base, "username": user[:3] + "***"}

    async def fetch_raw(self, input_data: Any, params: Dict) -> Any:
        data = input_data if isinstance(input_data, dict) else {}
        case_number = params.get("case_number") or data.get("case_number")
        court_id = params.get("court_id") or data.get("court_id", "uscourts")
        if not case_number:
            raise ValueError("case_number is required for PACER search")

        base = self._base_url()
        user, password = self._credentials()
        url = f"{base}/api/v1/cases/search"
        timeout = float(self.config.get("timeout_seconds", 30))

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(
                url,
                params={"caseNumber": case_number, "courtId": court_id},
                auth=(user, password) if user and password else None,
            )
            if resp.status_code == 404:
                return {
                    "stub": True,
                    "case_number": case_number,
                    "court_id": court_id,
                    "filings": [],
                    "message": "PACER endpoint not configured — returning stub response",
                }
            resp.raise_for_status()
            return resp.json()

    def normalize(
        self, raw: Any, params: Optional[Dict] = None, input_data: Any = None
    ) -> ConnectorEvent:
        data = input_data if isinstance(input_data, dict) else {}
        case_number = (params or {}).get("case_number") or data.get("case_number", "")
        filings = []
        if isinstance(raw, dict):
            filings = raw.get("filings") or raw.get("results") or []
        return ConnectorEvent(
            source=self.connector_source,
            event_type="pacer.case.searched",
            payload=raw if isinstance(raw, dict) else {"data": raw},
            normalized_data={
                "case_number": case_number,
                "count": len(filings) if isinstance(filings, list) else 0,
                "filings": filings,
            },
            tags=["law", "pacer", "court"],
        )
