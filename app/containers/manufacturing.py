"""Manufacturing Container - manufacturing domain container v1.0.

Wraps ManufacturingBlockV2 and routes domain actions. Accepts user custom rules
injection through params["custom_rules"].
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from app.core.universal_base import UniversalContainer

logger = logging.getLogger(__name__)


class ManufacturingContainer(UniversalContainer):
    """
    Manufacturing Container: manufacturing document analysis, entity extraction,
    metrics, compliance checks, and risk scoring.
    """

    name = "manufacturing"
    version = "1.0"
    description = "Manufacturing document analysis, compliance, and risk scoring"
    layer = 3
    tags = ["domain", "container", "manufacturing"]
    requires = ["manufacturing_v2"]

    default_config = {
        "confidence_threshold": 0.85,
    }

    ui_schema = {
        "input": {
            "type": "text",
            "placeholder": "Paste manufacturing document text or chain from PDF/OCR...",
            "multiline": True,
        },
        "output": {
            "type": "table",
            "fields": [
                {"name": "oee", "type": "number", "label": "OEE %"},
                {"name": "first_pass_yield", "type": "number", "label": "First Pass Yield %"},
                {"name": "scrap_rate", "type": "number", "label": "Scrap Rate %"},
                {"name": "cost_per_unit", "type": "number", "label": "Cost / Unit"},
                {"name": "quality_risk", "type": "number", "label": "Quality Risk"},
                {"name": "supply_chain_risk", "type": "number", "label": "Supply Chain Risk"},
                {"name": "equipment_risk", "type": "number", "label": "Equipment Risk"},
                {"name": "confidence", "type": "percentage", "label": "Confidence"},
            ],
        },
        "quick_actions": [
            {"icon": "📄", "label": "Analyze BOM", "prompt": "Analyze this bill of materials"},
            {"icon": "🏭", "label": "Check ISO 9001 Compliance", "prompt": "Check this document for ISO 9001 compliance"},
            {"icon": "⚠️", "label": "Score Manufacturing Risks", "prompt": "Score manufacturing risks for this document"},
            {"icon": "🔍", "label": "Extract Parts & Defects", "prompt": "Extract parts and defects from this document"},
        ],
    }

    # ------------------------------------------------------------------
    # ACTION ROUTING
    # ------------------------------------------------------------------

    async def route(self, action: str, input_data: Any, params: Dict) -> Dict:
        """Route to internal manufacturing action handlers."""
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        action = data.get("action") or p.get("action") or action

        handlers = {
            "analyze": self._analyze,
            "extract_entities": self._extract_entities,
            "calculate_metrics": self._calculate_metrics,
            "check_compliance": self._check_compliance,
            "score_risk": self._score_risk,
            "health": self._health,
            "status": self._health,
        }

        handler = handlers.get(action)
        if not handler:
            return {
                "status": "error",
                "error": f"Unknown action: {action}",
                "known_actions": sorted(handlers.keys()),
            }

        return await handler(input_data, p)

    def get_actions(self) -> Dict[str, Callable]:
        """Return action name → handler mapping."""
        return {
            "analyze": self._analyze,
            "extract_entities": self._extract_entities,
            "calculate_metrics": self._calculate_metrics,
            "check_compliance": self._check_compliance,
            "score_risk": self._score_risk,
            "health": self._health,
        }

    # ------------------------------------------------------------------
    # BLOCK RESOLUTION
    # ------------------------------------------------------------------

    def _resolve_block(self, name: str):
        """Resolve a block by dependency injection, platform singleton, or registry."""
        block = self.get_dep(name)
        if block is not None:
            return block
        try:
            from app.dependencies import get_block_instance
            return get_block_instance(name)
        except Exception:
            pass
        try:
            from app.blocks import BLOCK_REGISTRY

            block_cls = BLOCK_REGISTRY.get(name)
            return block_cls() if block_cls else None
        except Exception:
            return None

    # ------------------------------------------------------------------
    # HANDLERS
    # ------------------------------------------------------------------

    async def _analyze(self, input_data: Any, params: Dict) -> Dict:
        """Run full ManufacturingBlockV2 analysis."""
        block = self._resolve_block("manufacturing_v2")
        if block is None:
            return {"status": "error", "error": "%s_v2 block unavailable" % self.name}
        return await block.process(input_data, params)

    async def _extract_entities(self, input_data: Any, params: Dict) -> Dict:
        """Extract manufacturing entities only."""
        result = await self._analyze(input_data, params)
        if result.get("status") == "error":
            return result
        return {
            "status": "success",
            "entities": result.get("entities", {}),
            "confidence": result.get("confidence", 0),
        }

    async def _calculate_metrics(self, input_data: Any, params: Dict) -> Dict:
        """Calculate manufacturing metrics only."""
        result = await self._analyze(input_data, params)
        if result.get("status") == "error":
            return result
        return {
            "status": "success",
            "metrics": result.get("metrics", {}),
            "financials": result.get("financials", {}),
            "confidence": result.get("confidence", 0),
        }

    async def _check_compliance(self, input_data: Any, params: Dict) -> Dict:
        """Check compliance flags only."""
        result = await self._analyze(input_data, params)
        if result.get("status") == "error":
            return result
        return {
            "status": "success",
            "compliance_flags": result.get("compliance_flags", {}),
            "custom_rule_hits": result.get("custom_rule_hits", []),
            "confidence": result.get("confidence", 0),
        }

    async def _score_risk(self, input_data: Any, params: Dict) -> Dict:
        """Score manufacturing risks only."""
        result = await self._analyze(input_data, params)
        if result.get("status") == "error":
            return result
        return {
            "status": "success",
            "risk_scores": result.get("risk_scores", {}),
            "confidence": result.get("confidence", 0),
        }

    async def _health(self, input_data: Any, params: Dict) -> Dict:
        """Container health check."""
        return {
            "status": "healthy",
            "container": self.name,
            "version": self.version,
        }

    # ------------------------------------------------------------------
    # CUSTOM RULES INJECTION
    # ------------------------------------------------------------------

    def _load_custom_rules(self, input_data: Any, params: Dict) -> List[Dict]:
        """Collect user custom rules from params or input_data."""
        data = input_data if isinstance(input_data, dict) else {}
        rules = params.get("custom_rules") or params.get("rules") or data.get("custom_rules") or data.get("rules")
        if isinstance(rules, list):
            return rules
        return []
