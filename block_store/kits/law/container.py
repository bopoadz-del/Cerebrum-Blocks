"""Law & Legal Practice Suite — domain container stub."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict

from app.containers.base import DomainContainer


class LawContainer(DomainContainer):
    name = "law"
    description = "Contract analysis, case research, and legal document intelligence blocks."
    version = "0.0.0-skeleton"
    system_prompt_file = "law_expert.txt"

    def __init__(self, kit_root: Path | None = None) -> None:
        self.kit_root = kit_root or Path(__file__).resolve().parent

    def get_actions(self) -> Dict[str, Callable]:
        return {
            "pacer_search": self._pacer_search,
            "caselaw_search": self._caselaw_search,
            "health": self._health,
        }

    async def _health(self, input_data: Any, params: Dict) -> Dict:
        return {"status": "healthy", "container": self.name, "version": self.version}

    async def _pacer_search(self, input_data: Any, params: Dict) -> Dict:
        block = self._resolve_block("pacer_connector")
        if block is None:
            return {"status": "error", "error": "pacer_connector block unavailable"}
        data = input_data if isinstance(input_data, dict) else {}
        merged = {**data, **(params or {})}
        merged.setdefault("action", "fetch")
        return await block.process(merged, {"action": "fetch", "case_number": merged.get("case_number")})

    async def _caselaw_search(self, input_data: Any, params: Dict) -> Dict:
        block = self._resolve_block("caselaw_connector")
        if block is None:
            return {"status": "error", "error": "caselaw_connector block unavailable"}
        data = input_data if isinstance(input_data, dict) else {}
        merged = {**data, **(params or {})}
        merged.setdefault("action", "fetch")
        return await block.process(merged, {"action": "fetch", "query": merged.get("query")})
