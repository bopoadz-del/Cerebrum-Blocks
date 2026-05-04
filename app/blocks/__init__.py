"""Platform Blocks — Construction Intelligence Platform."""

from app.core.universal_base import UniversalBlock, UniversalContainer
from app.core.typed_block import TypedBlock

# ── Document Extraction ──────────────────────────────────────────────────────
from .pdf import PDFBlock
from .pdf_v2 import PDFBlockV2
from .ocr import OCRBlock
from .ocr_v2 import OCRBlockV2
from .image import ImageBlock
from .document_engine import DocumentEngineBlock

# ── AI / Language ─────────────────────────────────────────────────────────────
from .chat import ChatBlock
from .translate import TranslateBlock
from .voice import VoiceBlock
from .web import WebBlock
from .search import SearchBlock
from .llm_enhancer import LLMEnhancerBlock

# ── Construction Intelligence ─────────────────────────────────────────────────
from .boq_processor import BOQProcessorBlock
from .bim_extractor import BIMExtractorBlock
from .bim import BIMBlock
from .drawing_qto import DrawingQTOBlock
from .primavera_parser import PrimaveraParserBlock
from .spec_analyzer import SpecAnalyzerBlock
from .formula_executor import FormulaExecutorBlock
from .sympy_reasoning import SymPyReasoningBlock
from .historical_benchmark import HistoricalBenchmarkBlock
from .smart_orchestrator import SmartOrchestratorBlock
from .construction_v2 import ConstructionBlockV2
from .recommendation_template import RecommendationTemplateBlock

# ── File Access ───────────────────────────────────────────────────────────────
from .local_drive import LocalDriveBlock
from .google_drive import GoogleDriveBlock
from .onedrive import OneDriveBlock
from .android_drive import AndroidDriveBlock
from .storage import StorageBlock
from .file_hasher import FileHasherBlock

# ── Search & Memory ───────────────────────────────────────────────────────────
from .vector_search import VectorSearchBlock
from .zvec import ZvecBlock
from .cache_manager import CacheManagerBlock
from .context_broker import ContextBrokerBlock

# ── Integration Blocks ────────────────────────────────────────────────────────
from .capture import CaptureBlock
from .agent_swarm import AgentSwarmBlock
from .workflow import WorkflowBlock
from .knowledge import KnowledgeBlock
from .orchestrator import OrchestratorBlock
from .queue import QueueBlock

# ── Platform / Admin ──────────────────────────────────────────────────────────
from .auth import AuthBlock
from .audit import AuditBlock
from .team import TeamBlock
from .version import VersionBlock
from .health_check import HealthCheckBlock
from .monitoring import MonitoringBlock
from .rate_limiter import RateLimiterBlock
from .validation import ValidationBlock
from .error_tracking import ErrorTrackingBlock

# ── Communication ─────────────────────────────────────────────────────────────
from .webhook import WebhookBlock

# ── Intelligence / Analytics ──────────────────────────────────────────────────
from .analytics import AnalyticsBlock
from .discovery import DiscoveryBlock
from .learning_engine import LearningEngineBlock
from .dashboard import DashboardBlock

# ── Utilities ─────────────────────────────────────────────────────────────────
from .code import CodeBlock
from .sandbox import SandboxBlock
from .async_processor import AsyncProcessorBlock
from .failover import FailoverBlock
from .traffic_manager import TrafficManagerBlock
from .adaptive_router import AdaptiveRouterBlock
from .jetson_gateway import JetsonGatewayBlock

# ── Marketplace ───────────────────────────────────────────────────────────────
from .review import ReviewBlock
from .payment_split import PaymentSplitBlock
from .documentation import DocumentationBlock

# ── Main Construction Container ───────────────────────────────────────────────
from app.containers import ConstructionContainer


BLOCK_REGISTRY = {
    # Document Extraction
    "pdf":              PDFBlock,
    "pdf_v2":           PDFBlockV2,
    "ocr":              OCRBlock,
    "ocr_v2":           OCRBlockV2,
    "image":            ImageBlock,
    "document_engine":  DocumentEngineBlock,

    # AI / Language
    "chat":             ChatBlock,
    "translate":        TranslateBlock,
    "voice":            VoiceBlock,
    "web":              WebBlock,
    "search":           SearchBlock,
    "llm_enhancer":     LLMEnhancerBlock,

    # Construction Intelligence
    "construction":         ConstructionContainer,
    "construction_v2":      ConstructionBlockV2,
    "boq_processor":        BOQProcessorBlock,
    "bim":                  BIMBlock,
    "bim_extractor":        BIMExtractorBlock,
    "drawing_qto":          DrawingQTOBlock,
    "primavera_parser":     PrimaveraParserBlock,
    "spec_analyzer":        SpecAnalyzerBlock,
    "formula_executor":     FormulaExecutorBlock,
    "sympy_reasoning":      SymPyReasoningBlock,
    "historical_benchmark": HistoricalBenchmarkBlock,
    "smart_orchestrator":   SmartOrchestratorBlock,
    "recommendation_template": RecommendationTemplateBlock,

    # File Access
    "local_drive":      LocalDriveBlock,
    "google_drive":     GoogleDriveBlock,
    "onedrive":         OneDriveBlock,
    "android_drive":    AndroidDriveBlock,
    "storage":          StorageBlock,
    "file_hasher":      FileHasherBlock,

    # Search & Memory
    "vector_search":    VectorSearchBlock,
    "zvec":             ZvecBlock,
    "cache_manager":    CacheManagerBlock,
    "context_broker":   ContextBrokerBlock,

    # Integration
    "capture":          CaptureBlock,
    "agent_swarm":      AgentSwarmBlock,
    "workflow":         WorkflowBlock,
    "knowledge":        KnowledgeBlock,
    "orchestrator":     OrchestratorBlock,
    "queue":            QueueBlock,

    # Platform / Admin
    "auth":             AuthBlock,
    "audit":            AuditBlock,
    "team":             TeamBlock,
    "version":          VersionBlock,
    "health_check":     HealthCheckBlock,
    "monitoring":       MonitoringBlock,
    "rate_limiter":     RateLimiterBlock,
    "validation":       ValidationBlock,
    "error_tracking":   ErrorTrackingBlock,

    # Communication
    "webhook":          WebhookBlock,

    # Intelligence / Analytics
    "analytics":        AnalyticsBlock,
    "discovery":        DiscoveryBlock,
    "learning_engine":  LearningEngineBlock,
    "dashboard":        DashboardBlock,

    # Utilities
    "code":             CodeBlock,
    "sandbox":          SandboxBlock,
    "async_processor":  AsyncProcessorBlock,
    "failover":         FailoverBlock,
    "traffic_manager":  TrafficManagerBlock,
    "adaptive_router":  AdaptiveRouterBlock,
    "jetson_gateway":   JetsonGatewayBlock,

    # Marketplace
    "review":           ReviewBlock,
    "payment_split":    PaymentSplitBlock,
    "documentation":    DocumentationBlock,
}


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
