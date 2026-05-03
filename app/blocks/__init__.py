"""Platform Blocks - Universal Block System."""

from app.core.universal_base import UniversalBlock, UniversalContainer
from app.core.typed_block import TypedBlock

# Core AI Blocks (v1)
from .chat import ChatBlock
from .pdf import PDFBlock
from .ocr import OCRBlock
from .voice import VoiceBlock
from .vector_search import VectorSearchBlock
from .image import ImageBlock
from .translate import TranslateBlock
from .code import CodeBlock
from .web import WebBlock
from .search import SearchBlock
from .zvec import ZvecBlock

# Core AI Blocks (v2 - TypedBlock)
from .pdf_v2 import PDFBlockV2
from .ocr_v2 import OCRBlockV2
from .construction_v2 import ConstructionBlockV2

# Drive Blocks
from .google_drive import GoogleDriveBlock
from .onedrive import OneDriveBlock
from .local_drive import LocalDriveBlock
from .android_drive import AndroidDriveBlock

# Infrastructure Blocks
from .orchestrator import OrchestratorBlock
from .traffic_manager import TrafficManagerBlock
from .event_bus import EventBusBlock
from .context_broker import ContextBrokerBlock
from .cache_manager import CacheManagerBlock
from .async_processor import AsyncProcessorBlock
from .file_hasher import FileHasherBlock
from .llm_enhancer import LLMEnhancerBlock

# Document Engine
from .document_engine import DocumentEngineBlock

# Construction Intelligence Blocks
from .historical_benchmark import HistoricalBenchmarkBlock
from .boq_processor import BOQProcessorBlock

# Group 4: Advanced Construction Intelligence
from .bim_extractor import BIMExtractorBlock
from .drawing_qto import DrawingQTOBlock
from .formula_executor import FormulaExecutorBlock
from .jetson_gateway import JetsonGatewayBlock
from .learning_engine import LearningEngineBlock
from .primavera_parser import PrimaveraParserBlock
from .recommendation_template import RecommendationTemplateBlock
from .smart_orchestrator import SmartOrchestratorBlock
from .spec_analyzer import SpecAnalyzerBlock
from .sympy_reasoning import SymPyReasoningBlock

# Containers
from app.containers import ConstructionContainer

# Phase 5: Platform Blocks (ported from blocks/ registry)
from .adaptive_router import AdaptiveRouterBlock
from .analytics import AnalyticsBlock
from .audit import AuditBlock
from .auth import AuthBlock
from .billing import BillingBlock
from .bim import BIMBlock
from .config import ConfigBlock
from .container import ContainerBlock
from .container_ai_core import AICoreContainer
from .container_construction import ConstructionContainer as ConstructionContainerBlock
from .container_infrastructure import InfrastructureContainer
from .container_platform import PlatformContainer
from .container_security import SecurityContainer
from .container_store import StoreContainer
from .container_team import TeamContainer
from .container_utility import UtilityContainer
from .dashboard import DashboardBlock
from .database import DatabaseBlock
from .discovery import DiscoveryBlock
from .documentation import DocumentationBlock
from .email import EmailBlock
from .error_tracking import ErrorTrackingBlock
from .failover import FailoverBlock
from .health_check import HealthCheckBlock
from .memory import MemoryBlock
from .migration import MigrationBlock
from .monitoring import MonitoringBlock
from .notification import NotificationBlock
from .payment_split import PaymentSplitBlock
from .queue import QueueBlock
from .rate_limiter import RateLimiterBlock
from .review import ReviewBlock
from .sandbox import SandboxBlock
from .secrets import SecretsBlock
from .storage import StorageBlock
from .team import TeamBlock
from .validation import ValidationBlock
from .vector import VectorBlock
from .version import VersionBlock
from .webhook import WebhookBlock
from .workflow import WorkflowBlock

# Unified Registry
BLOCK_REGISTRY = {
    # Core AI (v1 - backward compatible)
    "chat": ChatBlock,
    "pdf": PDFBlock,
    "ocr": OCRBlock,
    "voice": VoiceBlock,
    "vector_search": VectorSearchBlock,
    "image": ImageBlock,
    "translate": TranslateBlock,
    "code": CodeBlock,
    "web": WebBlock,
    "search": SearchBlock,
    "zvec": ZvecBlock,

    # Core AI (v2 - TypedBlock)
    "pdf_v2": PDFBlockV2,
    "ocr_v2": OCRBlockV2,
    "construction_v2": ConstructionBlockV2,

    # Drive Blocks
    "google_drive": GoogleDriveBlock,
    "onedrive": OneDriveBlock,
    "local_drive": LocalDriveBlock,
    "android_drive": AndroidDriveBlock,

    # Infrastructure
    "orchestrator": OrchestratorBlock,
    "traffic_manager": TrafficManagerBlock,
    "event_bus": EventBusBlock,
    "context_broker": ContextBrokerBlock,
    "cache_manager": CacheManagerBlock,
    "async_processor": AsyncProcessorBlock,
    "file_hasher": FileHasherBlock,
    "llm_enhancer": LLMEnhancerBlock,

    # Document Engine
    "document_engine": DocumentEngineBlock,

    # Construction Intelligence Blocks
    "historical_benchmark": HistoricalBenchmarkBlock,
    "boq_processor": BOQProcessorBlock,

    # Group 4: Advanced Construction Intelligence
    "bim_extractor": BIMExtractorBlock,
    "drawing_qto": DrawingQTOBlock,
    "formula_executor": FormulaExecutorBlock,
    "jetson_gateway": JetsonGatewayBlock,
    "learning_engine": LearningEngineBlock,
    "primavera_parser": PrimaveraParserBlock,
    "recommendation_template": RecommendationTemplateBlock,
    "smart_orchestrator": SmartOrchestratorBlock,
    "spec_analyzer": SpecAnalyzerBlock,
    "sympy_reasoning": SymPyReasoningBlock,

    # Containers
    "construction": ConstructionContainer,

    # Phase 5: Platform Blocks
    "adaptive_router": AdaptiveRouterBlock,
    "analytics": AnalyticsBlock,
    "audit": AuditBlock,
    "auth": AuthBlock,
    "billing": BillingBlock,
    "bim": BIMBlock,
    "config": ConfigBlock,
    "container": ContainerBlock,
    "container_ai_core": AICoreContainer,
    "container_construction": ConstructionContainerBlock,
    "container_infrastructure": InfrastructureContainer,
    "container_platform": PlatformContainer,
    "container_security": SecurityContainer,
    "container_store": StoreContainer,
    "container_team": TeamContainer,
    "container_utility": UtilityContainer,
    "dashboard": DashboardBlock,
    "database": DatabaseBlock,
    "discovery": DiscoveryBlock,
    "documentation": DocumentationBlock,
    "email": EmailBlock,
    "error_tracking": ErrorTrackingBlock,
    "failover": FailoverBlock,
    "health_check": HealthCheckBlock,
    "memory": MemoryBlock,
    "migration": MigrationBlock,
    "monitoring": MonitoringBlock,
    "notification": NotificationBlock,
    "payment_split": PaymentSplitBlock,
    "queue": QueueBlock,
    "rate_limiter": RateLimiterBlock,
    "review": ReviewBlock,
    "sandbox": SandboxBlock,
    "secrets": SecretsBlock,
    "storage": StorageBlock,
    "team": TeamBlock,
    "validation": ValidationBlock,
    "vector": VectorBlock,
    "version": VersionBlock,
    "webhook": WebhookBlock,
    "workflow": WorkflowBlock,
}

def get_block(name: str):
    """Get a block class by name"""
    return BLOCK_REGISTRY.get(name)


def get_all_blocks():
    """Get all registered blocks"""
    return BLOCK_REGISTRY


__all__ = [
    "UniversalBlock",
    "UniversalContainer", 
    "TypedBlock",
    "BLOCK_REGISTRY",
    "get_block",
    "get_all_blocks",
]
