"""IoT sensor ingest connector — normalizes readings to ConnectorEvent."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.blocks.core.base_connector import BaseConnector
from app.core.connector_events import ConnectorEvent


class IotSensorConnectorBlock(BaseConnector):
    """Stub for IoT sensor telemetry ingest and normalization."""

    name = "iot_sensor_connector"
    version = "0.1.0-skeleton"
    description = "IoT sensor telemetry ingest connector (stub)"
    layer = 3
    tags = ["maintenance", "connector", "iot", "sensor", "telemetry", "stub"]
    connector_source = "iot_sensor"

    default_config = {
        "iot_gateway_url": os.getenv("IOT_GATEWAY_URL", ""),
        "iot_api_key": os.getenv("IOT_API_KEY", ""),
    }

    ui_schema = {
        "input": {
            "type": "json",
            "placeholder": '{"readings": [{"sensor_id": "temp-01", "metric": "temperature", "value": 22.5, "unit": "C"}]}',
            "multiline": True,
        },
        "output": {
            "type": "json",
            "fields": [
                {"name": "event", "type": "json", "label": "Connector Event"},
                {"name": "readings", "type": "json", "label": "Sensor Readings"},
            ],
        },
        "params": [
            {"name": "action", "type": "select", "label": "Action", "options": ["fetch", "ingest", "health"], "default": "ingest"},
            {"name": "sensor_id", "type": "text", "label": "Sensor ID"},
        ],
        "quick_actions": [
            {"icon": "📡", "label": "Ingest sensors", "prompt": "Ingest IoT sensor readings"},
        ],
    }

    async def authenticate(self) -> Dict[str, Any]:
        gateway = self.config.get("iot_gateway_url") or os.getenv("IOT_GATEWAY_URL", "")
        if gateway:
            return {"authenticated": True, "method": "api_key", "gateway": gateway}
        return {"authenticated": True, "method": "local_ingest"}

    async def fetch_raw(self, input_data: Any, params: Dict) -> Any:
        data = input_data if isinstance(input_data, dict) else {}
        action = params.get("action") or data.get("action", "ingest")

        if action == "ingest":
            readings = data.get("readings") or []
            if not readings and data.get("sensor_id"):
                readings = [data]
            if not readings:
                raise ValueError("readings array or sensor_id required for ingest")
            return {"readings": readings, "ingested_at": datetime.now(timezone.utc).isoformat()}

        sensor_id = params.get("sensor_id") or data.get("sensor_id")
        gateway = self.config.get("iot_gateway_url") or os.getenv("IOT_GATEWAY_URL", "")
        if not gateway or not sensor_id:
            return {
                "stub": True,
                "sensor_id": sensor_id or "sensor-stub",
                "readings": [
                    {
                        "sensor_id": sensor_id or "sensor-stub",
                        "metric": "temperature",
                        "value": 21.0,
                        "unit": "C",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ],
            }

        import httpx

        key = self.config.get("iot_api_key") or os.getenv("IOT_API_KEY", "")
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        url = f"{gateway.rstrip('/')}/sensors/{sensor_id}/readings"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    def normalize(
        self, raw: Any, params: Optional[Dict] = None, input_data: Any = None
    ) -> ConnectorEvent:
        readings: List[Dict[str, Any]] = []
        if isinstance(raw, dict):
            readings = raw.get("readings") or []
            if not readings and raw.get("sensor_id"):
                readings = [raw]

        normalized = []
        for r in readings:
            if not isinstance(r, dict):
                continue
            normalized.append({
                "sensor_id": r.get("sensor_id", "unknown"),
                "metric": r.get("metric", "unknown"),
                "value": r.get("value"),
                "unit": r.get("unit"),
                "timestamp": r.get("timestamp") or datetime.now(timezone.utc).isoformat(),
                "asset_id": r.get("asset_id"),
                "location": r.get("location"),
            })

        return ConnectorEvent(
            source=self.connector_source,
            event_type="iot.sensor.ingested",
            payload=raw if isinstance(raw, dict) else {"data": raw},
            normalized_data={
                "count": len(normalized),
                "readings": normalized,
            },
            tags=["maintenance", "iot", "sensor"],
        )

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        params = params or {}
        data = input_data if isinstance(input_data, dict) else {}
        action = params.get("action") or data.get("action", "ingest")
        if action == "health":
            return {"status": "healthy", "connector": self.connector_source, "block": self.name}
        if action == "ingest":
            params = {**params, "action": "ingest"}
        return await super().process(input_data, params)
