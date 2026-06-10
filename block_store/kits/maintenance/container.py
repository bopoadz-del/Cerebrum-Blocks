"""Maintenance & Facilities Suite — domain container stub."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict

from app.containers.base import DomainContainer


class MaintenanceContainer(DomainContainer):
    name = "maintenance"
    description = "Work orders, asset lifecycle, and preventive maintenance blocks."
    version = "0.0.0-skeleton"
    system_prompt_file = "maintenance_expert.txt"

    def __init__(self, kit_root: Path | None = None) -> None:
        self.kit_root = kit_root or Path(__file__).resolve().parent

    def get_actions(self) -> Dict[str, Callable]:
        return {
            "cmms_fetch": self._cmms_fetch,
            "sensor_ingest": self._sensor_ingest,
            "health": self._health,
        }

    async def _health(self, input_data: Any, params: Dict) -> Dict:
        return {"status": "healthy", "container": self.name, "version": self.version}

    async def _cmms_fetch(self, input_data: Any, params: Dict) -> Dict:
        block = self._resolve_block("cmms_connector")
        if block is None:
            return {"status": "error", "error": "cmms_connector block unavailable"}
        data = input_data if isinstance(input_data, dict) else {}
        merged = {**data, **(params or {})}
        return await block.process(merged, {"action": "fetch"})

    async def _sensor_ingest(self, input_data: Any, params: Dict) -> Dict:
        block = self._resolve_block("iot_sensor_connector")
        if block is None:
            return {"status": "error", "error": "iot_sensor_connector block unavailable"}
        data = input_data if isinstance(input_data, dict) else {}
        merged = {**data, **(params or {})}
        return await block.process(merged, {"action": "ingest"})
