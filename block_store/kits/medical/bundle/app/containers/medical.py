"""Medical Container - Healthcare domain container v1.0.

Wraps MedicalBlockV2 and routes domain actions. Accepts user custom rules
injection through params["custom_rules"].
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from app.core.universal_base import UniversalContainer

logger = logging.getLogger(__name__)


class MedicalContainer(UniversalContainer):
    """
    Medical Container: Healthcare document analysis, entity extraction,
    clinical metrics, compliance checks, and risk scoring.
    """

    name = "medical"
    version = "1.0"
    description = "Healthcare document analysis, clinical metrics, compliance, and risk scoring"
    layer = 3
    tags = ["domain", "container", "medical", "healthcare", "phi-safe"]
    requires = ["medical_v2"]

    default_config = {
        "confidence_threshold": 0.85,
        "redact_phi": True,
    }

    ui_schema = {
        "input": {
            "type": "text",
            "placeholder": "Paste medical document text or chain from PDF/OCR...",
            "multiline": True,
        },
        "output": {
            "type": "table",
            "fields": [
                {"name": "bmi", "type": "number", "label": "BMI"},
                {"name": "egfr", "type": "number", "label": "eGFR", "unit": "mL/min/1.73m²"},
                {"name": "cardiac_risk", "type": "percentage", "label": "Cardiac Risk"},
                {"name": "glasgow_score", "type": "number", "label": "GCS"},
                {"name": "readmission_risk", "type": "number", "label": "Readmission Risk"},
                {"name": "medication_error_risk", "type": "number", "label": "Med Error Risk"},
                {"name": "infection_risk", "type": "number", "label": "Infection Risk"},
                {"name": "confidence", "type": "percentage", "label": "Confidence"},
            ],
        },
        "quick_actions": [
            {"icon": "📝", "label": "Analyze Clinical Note", "prompt": "Analyze this clinical note"},
            {"icon": "🔒", "label": "Check HIPAA Compliance", "prompt": "Check this document for HIPAA compliance"},
            {"icon": "⚠️", "label": "Score Clinical Risks", "prompt": "Score clinical risks for this patient document"},
            {"icon": "💊", "label": "Extract Medications", "prompt": "Extract medications and dosages from this document"},
        ],
    }

    # ------------------------------------------------------------------
    # ACTION ROUTING
    # ------------------------------------------------------------------

    async def route(self, action: str, input_data: Any, params: Dict) -> Dict:
        """Route to internal medical action handlers."""
        data = input_data if isinstance(input_data, dict) else {}
        p = params or {}
        action = action or p.get("action") or data.get("action")

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
        """Run full MedicalBlockV2 analysis."""
        block = self._resolve_block("medical_v2")
        if block is None:
            return {"status": "error", "error": "medical_v2 block unavailable"}
        return await block.process(input_data, params)

    async def _extract_entities(self, input_data: Any, params: Dict) -> Dict:
        """Extract medical entities only."""
        result = await self._analyze(input_data, params)
        if result.get("status") == "error":
            return result
        return {
            "status": "success",
            "entities": result.get("entities", {}),
            "confidence": result.get("confidence", 0),
        }

    async def _calculate_metrics(self, input_data: Any, params: Dict) -> Dict:
        """Calculate clinical metrics only."""
        result = await self._analyze(input_data, params)
        if result.get("status") == "error":
            return result
        return {
            "status": "success",
            "clinical_metrics": result.get("clinical_metrics", {}),
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
        """Score clinical risks only."""
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
