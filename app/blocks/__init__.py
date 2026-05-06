"""Platform Blocks — Construction Intelligence Platform.

Block classes are imported lazily on first access from BLOCK_REGISTRY.
This keeps cold-start memory low — Render Starter (512MB) was OOMing on the
old eager-import path because each block module pulled in heavy ML deps
(sklearn, sympy, ezdxf, ifcopenshell, opencv, etc.).
"""

import importlib
import logging
from typing import Any, Dict, Iterator, Tuple

from app.core.universal_base import UniversalBlock, UniversalContainer
from app.core.typed_block import TypedBlock

logger = logging.getLogger(__name__)


# Map block name → (module path, class name). Modules import only on first access.
_BLOCK_DEFS: Dict[str, Tuple[str, str]] = {
    # Document Extraction
    "pdf":              ("app.blocks.pdf", "PDFBlock"),
    "pdf_v2":           ("app.blocks.pdf_v2", "PDFBlockV2"),
    "ocr":              ("app.blocks.ocr", "OCRBlock"),
    "ocr_v2":           ("app.blocks.ocr_v2", "OCRBlockV2"),
    "image":            ("app.blocks.image", "ImageBlock"),
    "document_engine":  ("app.blocks.document_engine", "DocumentEngineBlock"),

    # AI / Language
    "chat":             ("app.blocks.chat", "ChatBlock"),
    "translate":        ("app.blocks.translate", "TranslateBlock"),
    "voice":            ("app.blocks.voice", "VoiceBlock"),
    "web":              ("app.blocks.web", "WebBlock"),
    "search":           ("app.blocks.search", "SearchBlock"),
    "llm_enhancer":     ("app.blocks.llm_enhancer", "LLMEnhancerBlock"),

    # Construction Intelligence
    "construction":         ("app.containers", "ConstructionContainer"),
    "construction_v2":      ("app.blocks.construction_v2", "ConstructionBlockV2"),
    "boq_processor":        ("app.blocks.boq_processor", "BOQProcessorBlock"),
    "bim":                  ("app.blocks.bim", "BIMBlock"),
    "bim_extractor":        ("app.blocks.bim_extractor", "BIMExtractorBlock"),
    "drawing_qto":          ("app.blocks.drawing_qto", "DrawingQTOBlock"),
    "primavera_parser":     ("app.blocks.primavera_parser", "PrimaveraParserBlock"),
    "spec_analyzer":        ("app.blocks.spec_analyzer", "SpecAnalyzerBlock"),
    "formula_executor":     ("app.blocks.formula_executor", "FormulaExecutorBlock"),
    "sympy_reasoning":      ("app.blocks.sympy_reasoning", "SymPyReasoningBlock"),
    "historical_benchmark": ("app.blocks.historical_benchmark", "HistoricalBenchmarkBlock"),
    "smart_orchestrator":   ("app.blocks.smart_orchestrator", "SmartOrchestratorBlock"),
    "skills":               ("app.blocks.skills", "SkillsBlock"),
    "recommendation_template": ("app.blocks.recommendation_template", "RecommendationTemplateBlock"),

    # File Access
    "local_drive":      ("app.blocks.local_drive", "LocalDriveBlock"),
    "google_drive":     ("app.blocks.google_drive", "GoogleDriveBlock"),
    "onedrive":         ("app.blocks.onedrive", "OneDriveBlock"),
    "android_drive":    ("app.blocks.android_drive", "AndroidDriveBlock"),
    "storage":          ("app.blocks.storage", "StorageBlock"),
    "file_hasher":      ("app.blocks.file_hasher", "FileHasherBlock"),

    # Search & Memory
    "vector_search":    ("app.blocks.vector_search", "VectorSearchBlock"),
    "zvec":             ("app.blocks.zvec", "ZvecBlock"),
    "cache_manager":    ("app.blocks.cache_manager", "CacheManagerBlock"),
    "context_broker":   ("app.blocks.context_broker", "ContextBrokerBlock"),

    # Integration
    "capture":          ("app.blocks.capture", "CaptureBlock"),
    "agent_swarm":      ("app.blocks.agent_swarm", "AgentSwarmBlock"),
    "workflow":         ("app.blocks.workflow", "WorkflowBlock"),
    "knowledge":        ("app.blocks.knowledge", "KnowledgeBlock"),
    "orchestrator":     ("app.blocks.orchestrator", "OrchestratorBlock"),
    "queue":            ("app.blocks.queue", "QueueBlock"),

    # Platform / Admin
    "auth":             ("app.blocks.auth", "AuthBlock"),
    "audit":            ("app.blocks.audit", "AuditBlock"),
    "team":             ("app.blocks.team", "TeamBlock"),
    "version":          ("app.blocks.version", "VersionBlock"),
    "health_check":     ("app.blocks.health_check", "HealthCheckBlock"),
    "monitoring":       ("app.blocks.monitoring", "MonitoringBlock"),
    "rate_limiter":     ("app.blocks.rate_limiter", "RateLimiterBlock"),
    "validation":       ("app.blocks.validation", "ValidationBlock"),
    "error_tracking":   ("app.blocks.error_tracking", "ErrorTrackingBlock"),

    # Communication
    "webhook":          ("app.blocks.webhook", "WebhookBlock"),
    "notification":     ("app.blocks.notification", "NotificationBlock"),

    # Intelligence / Analytics
    "analytics":        ("app.blocks.analytics", "AnalyticsBlock"),
    "discovery":        ("app.blocks.discovery", "DiscoveryBlock"),
    "learning_engine":  ("app.blocks.learning_engine", "LearningEngineBlock"),
    "dashboard":        ("app.blocks.dashboard", "DashboardBlock"),

    # Utilities
    "code":             ("app.blocks.code", "CodeBlock"),
    "sandbox":          ("app.blocks.sandbox", "SandboxBlock"),
    "async_processor":  ("app.blocks.async_processor", "AsyncProcessorBlock"),
    "failover":         ("app.blocks.failover", "FailoverBlock"),
    "traffic_manager":  ("app.blocks.traffic_manager", "TrafficManagerBlock"),
    "adaptive_router":  ("app.blocks.adaptive_router", "AdaptiveRouterBlock"),
    "jetson_gateway":   ("app.blocks.jetson_gateway", "JetsonGatewayBlock"),

    # Marketplace
    "review":           ("app.blocks.review", "ReviewBlock"),
    "payment_split":    ("app.blocks.payment_split", "PaymentSplitBlock"),
    "documentation":    ("app.blocks.documentation", "DocumentationBlock"),

    # Infrastructure — these block files existed in app/blocks/ but were
    # never registered, so 31 dependent blocks (auth, audit, secrets, team,
    # validation, version, etc.) silently lost their `requires` deps.
    # Registered here as part of the same lazy mapping so dep wiring can
    # find them. They each have UniversalBlock-compatible signatures.
    "config":           ("app.blocks.config", "ConfigBlock"),
    "database":         ("app.blocks.database", "DatabaseBlock"),
    "vector":           ("app.blocks.vector", "VectorBlock"),
    "billing":          ("app.blocks.billing", "BillingBlock"),
    "email":            ("app.blocks.email", "EmailBlock"),
    "migration":        ("app.blocks.migration", "MigrationBlock"),
    "event_bus":        ("app.blocks.event_bus", "EventBusBlock"),
    "secrets":          ("app.blocks.secrets", "SecretsBlock"),
}


class _LazyBlockRegistry:
    """Dict-like view of block classes that imports each module on first access.

    Supports the subset of dict API the codebase actually uses:
    [name], .get(name), name in registry, .items(), .keys(), len(),
    iteration. .items() is lazy too — yields (name, class) pairs and forces
    import at the moment each pair is consumed. So `for name, cls in items()`
    DOES load every block, by design (e.g. init_blocks pass).
    """

    __slots__ = ("_resolved",)

    def __init__(self) -> None:
        self._resolved: Dict[str, Any] = {}

    def _resolve(self, name: str) -> Any:
        cached = self._resolved.get(name)
        if cached is not None:
            return cached
        if name not in _BLOCK_DEFS:
            raise KeyError(name)
        module_path, class_name = _BLOCK_DEFS[name]
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
        except Exception as exc:
            logger.exception("block import failed: %s (%s.%s) — %s",
                             name, module_path, class_name, exc)
            raise
        self._resolved[name] = cls
        return cls

    def __getitem__(self, name: str) -> Any:
        return self._resolve(name)

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and name in _BLOCK_DEFS

    def get(self, name: str, default: Any = None) -> Any:
        try:
            return self._resolve(name)
        except (KeyError, Exception):
            return default

    def keys(self) -> Iterator[str]:
        return iter(_BLOCK_DEFS.keys())

    def items(self) -> Iterator[Tuple[str, Any]]:
        for name in _BLOCK_DEFS:
            try:
                yield name, self._resolve(name)
            except Exception:
                continue  # skip blocks whose import fails

    def __iter__(self) -> Iterator[str]:
        return iter(_BLOCK_DEFS.keys())

    def __len__(self) -> int:
        return len(_BLOCK_DEFS)


BLOCK_REGISTRY = _LazyBlockRegistry()


def get_block(name: str):
    return BLOCK_REGISTRY.get(name)


def get_all_blocks():
    return BLOCK_REGISTRY


__all__ = [
    "UniversalBlock",
    "UniversalContainer",
    "TypedBlock",
    "BLOCK_REGISTRY",
    "get_block",
    "get_all_blocks",
]


# Build a fast reverse lookup so `from app.blocks import PDFBlock` (tests do this)
# resolves to the same class as BLOCK_REGISTRY["pdf"], with the same lazy import.
_CLASS_TO_NAME: Dict[str, str] = {
    class_name: block_name for block_name, (_, class_name) in _BLOCK_DEFS.items()
}


def __getattr__(name: str) -> Any:
    """Module-level lazy attribute access (PEP 562).

    Lets callers do `from app.blocks import PDFBlock` without forcing an
    eager import of every block at module load. Falls back to AttributeError
    for unknown names so the rest of Python's import machinery still works.
    """
    block_name = _CLASS_TO_NAME.get(name)
    if block_name is None:
        raise AttributeError(f"module 'app.blocks' has no attribute {name!r}")
    return BLOCK_REGISTRY[block_name]
