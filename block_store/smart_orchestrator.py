"""Smart Orchestrator Block - 53-action keyword router for construction workflows.

The runtime action list is built by prepending PROCEDURE_ROUTING_ADDITIONS
(17 procedure-specific actions, PRC-301..PRC-606) to the in-file
ACTION_PATTERNS list (41 entries). Six action names appear in both lists;
their keyword lists are MERGED at scoring time so neither source loses coverage.
Net unique actions: 17 + (41 - 6) = 52.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from app.core.universal_base import UniversalBlock
from app.blocks._procedure_routing import PROCEDURE_ROUTING_ADDITIONS


# Word-boundary keyword cache. Substring `kw in text` is unsafe — 2-char keys
# like "co" / "vo" match inside "concrete", "construction", "voltage", and so
# every chat message gets routed to change-order / variation-order actions.
_KW_REGEX_CACHE: Dict[str, "re.Pattern[str]"] = {}


def _kw_pattern(kw: str) -> "re.Pattern[str]":
    pat = _KW_REGEX_CACHE.get(kw)
    if pat is None:
        pat = re.compile(
            r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])",
            flags=re.IGNORECASE,
        )
        _KW_REGEX_CACHE[kw] = pat
    return pat


def _matches_keyword(kw: str, text: str) -> bool:
    return bool(_kw_pattern(kw).search(text))


# Fallback generative-intent set used when app.core.action_router is not present.
_GENERATIVE_INTENTS_FALLBACK = {
    "generate_wbs",
    "bim_analysis",
    "drawing_qto",
    "bim_extractor",
    "digital_twin_sync",
    "value_engineering",
    "intelligent_workflow",
}


ACTION_PATTERNS: List[Tuple[str, List[str]]] = PROCEDURE_ROUTING_ADDITIONS + [
    ("construction_advisor", [
        "mass concrete", "equilibrium time", "thermal control", "core temperature",
        "compaction acceptance", "field density", "proctor", "swelling factor",
        "dewatering", "well point", "ground improvement", "dynamic compaction",
        "soil stabilization", "roller compacted", "rcc mix", "bitumen content",
        "wearing course", "heavy lift", "crane lift", "lifting feasibility",
        "uplift", "factor of safety", "diaphragm wall", "post-tension",
        "sealant joint", "rebar coupler", "tunnel cross section",
        "earthworks production", "haul distance", "design formula",
    ]),
    ("boq_process",           ["boq", "bill of quantities", "bill of quantity", "quantities sheet", "cost sheet", "price list", ".xlsx", ".csv"]),
    ("generate_wbs",          [
        "wbs", "work breakdown",
        "activities schedule", "activity schedule",
        "200 activities", "300 activities", "400 activities", "500 activities",
        "100 activities", "150 activities", "250 activities", "350 activities",
        "schedule activities",
        "create schedule", "generate schedule", "build schedule", "draft schedule",
        "produce schedule", "make schedule", "develop schedule", "prepare schedule",
        "schedule template", "activity list",
        "l1 schedule", "l2 schedule", "l3 schedule", "l4 schedule",
        "level 1 schedule", "level 2 schedule", "level 3 schedule", "level 4 schedule",
        "construction schedule", "project schedule", "master schedule",
        "baseline schedule", "epc schedule",
    ]),
    ("extract_quantities",    ["extract quantities", "take off", "qto", "quantity take", "measure", "count items", "area calculation", "room area", "floor area", "calculate area", "quantities", "takeoff"]),
    ("estimate_costs",        ["estimate cost", "cost estimate", "budget", "pricing", "price estimate", "how much"]),
    ("tender_bid_analysis",   ["tender", "bid", "proposal", "quote comparison", "contractor bid",
                                "contractor bids", "compare bids", "score bids", "tender scoring", "evaluate bids"]),
    ("procurement_list_generator", ["procurement", "material list", "purchase list", "buy list", "vendor list", "procurement list", "what materials", "need to buy", "materials list"]),
    ("procurement_optimizer", ["optimize procurement", "best supplier", "cheapest", "optimize cost"]),
    ("payment_certificate",   ["payment cert", "valuation", "progress payment", "invoice", "certificate"]),
    ("cash_flow_forecast",    ["cash flow", "s-curve", "payment schedule", "fund flow", "s curve", "spend curve", "cumulative spend", "cumulative cost curve", "drawdown"]),
    ("spec_analyze",          ["spec", "specification", "material spec", "grade requirement", "astm", "aci", "saso", "standard", "compliance check", "specification requirements", "material specs", "material specifications", "concrete specification", "specs"]),
    ("process_specification_full", ["full specification", "spec section", "csi division", "masterformat"]),
    ("drawing_qto",           ["drawing", "dxf", "dwg", "floor plan", "blueprint", "autocad", "measure drawing", "drawings", "quantity takeoff", "takeoff", "take-off"]),
    ("parse_primavera_schedule", ["primavera", "xer", "p6", "schedule", "gantt", "programme", "baseline", "milestones", "milestone", "key milestones", "milestone report", "completion dates", "major completion dates"]),
    ("progress_tracker",      ["progress", "completion", "percent complete", "actual vs planned", "delay",
                                "progress tracking", "tracking against planned", "slipping", "behind schedule", "schedule slippage"]),
    ("resource_histogram",    ["resource", "manpower", "histogram", "crew", "labor loading", "workforce"]),
    ("forensic_delay_analysis", ["delay analysis", "eot", "extension of time", "delay claim", "forensic"]),
    ("bim_analysis",          ["bim", "ifc", "revit", "3d model", "building model", "navisworks"]),
    ("bim_clash_detection",   ["clash", "clash detection", "interference", "conflict", "mep conflict"]),
    ("bim_extractor",         ["extract bim", "ifc quantities", "bim quantities", "model quantities"]),
    ("digital_twin_sync",     ["digital twin", "asset data", "sync model", "as-built bim"]),
    ("qa_qc_inspection",      ["qa", "qc", "quality", "inspection", "test report", "ncr", "non-conformance", "punch list"]),
    ("commissioning_checklist", ["commissioning", "handover", "pre-commissioning", "startup checklist", "commissioning checklist", "commissioning steps", "t&c steps", "energising", "energisation", "energizing", "energization"]),
    ("process_contract",      ["contract", "subcontract", "agreement", "terms", "clause", "fidic", "nec"]),
    ("change_order_impact",   ["change order", "variation", "scope change", "amendment"]),
    ("variation_order_manager", ["variation order", "variation management", "change log"]),
    ("claims_builder",        ["claim", "dispute", "loss and expense", "damages", "extension of time"]),
    ("rfi_generator",         ["rfi", "request for information", "query", "clarification", "design query"]),
    ("safety_compliance_audit", ["safety", "hse", "osha", "risk assessment", "hazard", "ppe", "toolbox",
                                  "hse compliance audit", "working at height", "work at height", "fall protection",
                                  "site safety audit", "compliance audit checklist"]),
    ("risk_register_auto_populate", ["risk register", "risk log", "risk matrix", "risk assessment"]),
    ("carbon_footprint_calculator", ["carbon", "co2", "emissions", "sustainability", "embodied carbon", "lca"]),
    ("esg_sustainability_report", ["esg", "green", "leed", "breeam", "environmental report", "sustainability report"]),
    ("daily_site_report",     ["daily report", "site diary", "dsr", "site report", "daily log"]),
    ("submittal_log_generator", ["submittal", "transmittal", "document log", "material approval", "shop drawing",
                                  "submittal log", "submittal register", "approval status", "material submittal", "shop drawing submittal"]),
    ("as_built_deviation_report", ["as-built", "as built", "deviation", "red-line", "record drawing",
                                    "as-built deviations", "as built deviations", "deviations from design",
                                    "redline drawing", "as-built report"]),
    ("warranty_maintenance_schedule", ["warranty", "maintenance", "service schedule", "pppm", "o&m"]),
    ("om_manual_generator",   ["o&m", "operation manual", "maintenance manual", "handover manual",
                                "o&m manual", "operation and maintenance manual", "o&m outline", "o and m manual"]),
    ("value_engineering",     ["value engineering", "ve study", "cost reduction", "alternative", "optimization",
                                "value engineer", "value engineering options", "cut cost", "cost reduction options",
                                "optimize cost", "value engineering study"]),
    ("sympy_reason",          ["variance analysis", "reasoning", "compare cost", "benchmark", "symbolic", "formula"]),
    ("process_document",      ["document", "pdf", "report", "upload", "analyse file", "analyze file", "execution plan", "project execution plan", "what documents", "list the documents", "which documents", "which drawings", "project documents", "what files", "documents in this project"]),
    ("intelligent_workflow",  ["workflow", "automate", "chain", "pipeline", "multi-step", "full analysis"]),
    ("health_check",          ["health", "status", "ping", "alive", "system check"]),
]


FILE_TYPE_MAP: Dict[str, str] = {
    ".xlsx": "boq_process",
    ".xls":  "boq_process",
    ".csv":  "boq_process",
    ".xer":  "parse_primavera_schedule",
    ".ifc":  "bim_analysis",
    ".dxf":  "drawing_qto",
    ".dwg":  "drawing_qto",
    ".pdf":  "process_document",
    ".jpg":  "qa_qc_inspection",
    ".jpeg": "qa_qc_inspection",
    ".png":  "qa_qc_inspection",
}


PARALLEL_GROUPS: Dict[str, List[str]] = {
    "full_analysis": [
        "boq_process", "spec_analyze", "drawing_qto", "parse_primavera_schedule"
    ],
    "cost_suite": [
        "extract_quantities", "estimate_costs", "procurement_list_generator"
    ],
    "compliance_suite": [
        "spec_analyze", "qa_qc_inspection", "safety_compliance_audit"
    ],
    "reporting_suite": [
        "daily_site_report", "progress_tracker", "cash_flow_forecast"
    ],
}


class SmartOrchestratorBlock(UniversalBlock):
    auto_validate = False
    name = "smart_orchestrator"
    version = "1.1.0"
    updated_at = "2026-07-19"
    description = "52-action construction keyword router: maps user messages to action queues with parallel execution hints"
    layer = 2
    tags = ["infrastructure", "construction", "orchestration", "routing", "nlp"]
    requires = []
    allow_empty_input = True

    default_config = {
        "max_actions": 5,
        "confidence_threshold": 0.3,
        "generative_confidence_threshold": 0.2,
        "fallback_agent": "intelligent_workflow",
    }

    ui_schema = {
        "input": {
            "type": "text",
            "placeholder": "Describe what you need (e.g. 'analyze the BOQ and check specs')...",
            "multiline": True,
        },
        "output": {
            "type": "json",
            "fields": [
                {"name": "action_queue", "type": "list", "label": "Action Queue"},
                {"name": "parallel_flag", "type": "boolean", "label": "Run Parallel"},
                {"name": "fallback_agent", "type": "text", "label": "Fallback"},
            ],
        },
        "quick_actions": [
            {"icon": "🔀", "label": "Route Message", "prompt": "What actions should I run for this request?"},
            {"icon": "📋", "label": "List Actions", "prompt": "List all available construction actions"},
        ],
    }

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        params = params or {}
        data = input_data if isinstance(input_data, dict) else {}

        user_message = (
            data.get("user_message")
            or data.get("message")
            or data.get("text")
            or data.get("input")
            or (input_data if isinstance(input_data, str) else "")
        )
        session_context = data.get("session_context", {})
        file_type = (
            data.get("file_type")
            or params.get("file_type")
            or self._detect_file_type(data, session_context)
        )

        if str(user_message).strip().lower() in ("list actions", "help", "what can you do"):
            return self._list_actions()

        routing_mode = data.get("routing_mode") or params.get("routing_mode") or self.config.get("routing_mode", "keyword")
        learned_prediction: Optional[Dict[str, Any]] = None
        if routing_mode == "learned":
            learned_prediction = self._predict_learned(user_message)
            if learned_prediction and not learned_prediction.get("fallback_recommended"):
                action = learned_prediction["action"]
                action_queue = [action]
                max_actions = int(params.get("max_actions", self.config.get("max_actions", 5)))
                matched_secondary = self._match_actions(user_message, file_type)
                secondary = [m for m in matched_secondary if m["action"] != action][:max_actions - 1]
                action_queue.extend(m["action"] for m in secondary)

                parallel_group = self._detect_parallel_group(action_queue)
                parallel_flag = parallel_group is not None or len(action_queue) > 1
                fallback = self.config.get("fallback_agent", "intelligent_workflow")

                self._record_routing_decision(
                    user_message, action, learned_prediction["confidence"],
                    source="learned", session_context=session_context,
                )

                return {
                    "status": "success",
                    "action_queue": action_queue,
                    "parallel_flag": parallel_flag,
                    "parallel_group": parallel_group,
                    "fallback_agent": fallback,
                    "matched_actions": [{
                        "action": action,
                        "score": learned_prediction["confidence"],
                        "source": "learned",
                    }] + secondary,
                    "file_type_hint": file_type,
                    "session_context": session_context,
                    "routing_mode": "learned",
                    "model_confidence": learned_prediction["confidence"],
                    "fallback_used": False,
                    "top_k": learned_prediction.get("top_k", []),
                }

        matched = self._match_actions(user_message, file_type)
        max_actions = int(params.get("max_actions", self.config.get("max_actions", 5)))
        action_queue = [m["action"] for m in matched[:max_actions]]

        parallel_group = self._detect_parallel_group(action_queue)
        parallel_flag = parallel_group is not None or len(action_queue) > 1

        fallback = self.config.get("fallback_agent", "intelligent_workflow")
        if not action_queue:
            action_queue = [fallback]
            parallel_flag = False

        if routing_mode == "learned" and action_queue and action_queue[0] != fallback:
            self._record_routing_decision(
                user_message, action_queue[0],
                (matched[0].get("confidence", 0.0) if matched else 0.0),
                source="keyword_fallback", session_context=session_context,
            )

        return {
            "status": "success",
            "action_queue": action_queue,
            "parallel_flag": parallel_flag,
            "parallel_group": parallel_group,
            "fallback_agent": fallback,
            "matched_actions": matched[:max_actions],
            "file_type_hint": file_type,
            "session_context": session_context,
            "routing_mode": routing_mode,
            **({"fallback_used": True, "model_confidence": (learned_prediction or {}).get("confidence", 0.0),
                "fallback_reason": (learned_prediction or {}).get("reason")}
               if routing_mode == "learned" else {}),
        }

    def _predict_learned(self, message: str) -> Optional[Dict[str, Any]]:
        """Consult learning_engine's predict_route op. Returns None on any error."""
        from app.blocks import BLOCK_REGISTRY

        cls = BLOCK_REGISTRY.get("learning_engine")
        if cls is None:
            return None
        try:
            le = cls.shared_instance()
            return le._predict_route({"text": message}, {})
        except Exception:  # noqa: BLE001
            return None

    def _record_routing_decision(
        self, message: str, action: str, score: float,
        source: str, session_context: Dict,
    ) -> None:
        """Log the dispatch as a routing_decisions pattern on learning_engine."""
        import json
        from app.blocks import BLOCK_REGISTRY

        try:
            cls = BLOCK_REGISTRY.get("learning_engine")
            if cls is None:
                return
            le = cls.shared_instance()
            project_id = (session_context or {}).get("project_id") or "default"
            le._record_pattern({
                "project_id": project_id,
                "category": "routing_decisions",
                "observation": json.dumps({
                    "text": message[:500],
                    "action": action,
                    "score": float(score),
                    "source": source,
                    "corrected": False,
                }, ensure_ascii=False),
                "source": "smart_orchestrator",
            }, {})
        except Exception:  # noqa: BLE001
            pass

    def _match_actions(self, message: str, file_type: Optional[str]) -> List[Dict]:
        scores: Dict[str, float] = {}

        if file_type and file_type in FILE_TYPE_MAP:
            action = FILE_TYPE_MAP[file_type]
            scores[action] = scores.get(action, 0.0) + 0.8

        # Merge duplicate action names so every keyword is available.
        merged_patterns: Dict[str, List[str]] = {}
        for action, keywords in ACTION_PATTERNS:
            existing = merged_patterns.setdefault(action, [])
            for kw in keywords:
                if kw not in existing:
                    existing.append(kw)

        for action, keywords in merged_patterns.items():
            for kw in keywords:
                if _matches_keyword(kw, message):
                    # Base 0.3 for any keyword so short but specific tokens like
                    # "boq" / "xer" clear the default gate; multi-word phrases
                    # score higher to reward precise intent matches.
                    weight = 0.3 + (len(kw.split()) - 1) * 0.15
                    scores[action] = scores.get(action, 0.0) + weight

        # Optional per-action generative threshold. Fall back to a local set if
        # the platform action_router module is not present.
        try:
            from app.core.action_router import GENERATIVE_INTENTS
        except Exception:  # noqa: BLE001
            GENERATIVE_INTENTS = _GENERATIVE_INTENTS_FALLBACK

        threshold = float(self.config.get("confidence_threshold", 0.3))
        generative_threshold = float(
            self.config.get("generative_confidence_threshold", 0.2)
        )

        def _gate_for(action: str) -> float:
            return generative_threshold if action in GENERATIVE_INTENTS else threshold

        results = [
            {
                "action": action,
                "confidence": round(min(score, 1.0), 3),
                "keywords_matched": [
                    kw for kw in merged_patterns.get(action, [])
                    if _matches_keyword(kw, message)
                ],
            }
            for action, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)
            if score >= _gate_for(action)
        ]
        return results

    def _detect_file_type(self, data: Dict, context: Dict) -> Optional[str]:
        for key in ("file_path", "filename", "file"):
            val = data.get(key) or context.get(key, "")
            if val:
                ext = "." + str(val).rsplit(".", 1)[-1].lower() if "." in val else ""
                if ext in FILE_TYPE_MAP:
                    return ext
        return None

    def _detect_parallel_group(self, actions: List[str]) -> Optional[str]:
        action_set = set(actions)
        for group_name, group_actions in PARALLEL_GROUPS.items():
            if len(action_set & set(group_actions)) >= 2:
                return group_name
        return None

    def _list_actions(self) -> Dict:
        unique = list(dict.fromkeys(a for a, _ in ACTION_PATTERNS))
        return {
            "status": "success",
            "action_queue": [],
            "parallel_flag": False,
            "fallback_agent": self.config.get("fallback_agent", "intelligent_workflow"),
            "all_actions": unique,
            "total_actions": len(unique),
            "parallel_groups": PARALLEL_GROUPS,
            "file_type_routing": FILE_TYPE_MAP,
        }
