"""Platform Blocks - Universal Block System (Single Source of Truth)"""

from app.core.universal_base import UniversalBlock, UniversalContainer

# Core AI Blocks
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

# Drive Blocks
from .google_drive import GoogleDriveBlock
from .onedrive import OneDriveBlock
from .local_drive import LocalDriveBlock
from .android_drive import AndroidDriveBlock

# Construction Intelligence Blocks (Week 1)
from .sympy_reasoning import SymPyReasoningBlock
from .boq_processor import BOQProcessorBlock
from .spec_analyzer import SpecAnalyzerBlock

# Construction Domain Blocks (Week 2)
from .drawing_qto import DrawingQTOBlock
from .primavera_parser import PrimaveraParserBlock
from .smart_orchestrator import SmartOrchestratorBlock

# Intelligence Blocks (Week 3)
from .jetson_gateway import JetsonGatewayBlock
from .formula_executor import FormulaExecutorBlock
from .bim_extractor import BIMExtractorBlock

# Intelligence Blocks (Week 4)
from .learning_engine import LearningEngineBlock
from .historical_benchmark import HistoricalBenchmarkBlock
from .recommendation_template import RecommendationTemplateBlock

# ML Engine Block
from .ml_engine import MLEngineBlock

# Reasoning Engine Blocks
from .validator import ValidatorBlock
from .credibility_scorer import CredibilityScorerBlock
from .predictive_engine import PredictiveEngineBlock
from .evidence_vault import EvidenceVaultBlock

# Telegram Bot Block
from .telegram_bot import TelegramBotBlock

# Infrastructure Blocks
from .orchestrator import OrchestratorBlock
from .traffic_manager import TrafficManagerBlock
from .event_bus import EventBusBlock
from .context_broker import ContextBrokerBlock
from .llm_enhancer import LLMEnhancerBlock
from .cache_manager import CacheManagerBlock
from .async_processor import AsyncProcessorBlock
from .file_hasher import FileHasherBlock

# Domain Containers
from app.containers import (
    ConstructionContainer,
    MedicalContainer,
    LegalContainer,
    FinanceContainer,
    SecurityContainer,
    AICoreContainer,
    StoreContainer,
    LibrariesContainer,
    MLContainer,
    ReasoningEngineContainer,
)

# Unified Registry
BLOCK_REGISTRY = {
    # Core AI
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
    # Drive
    "google_drive": GoogleDriveBlock,
    "onedrive": OneDriveBlock,
    "local_drive": LocalDriveBlock,
    "android_drive": AndroidDriveBlock,
    # Construction Intelligence (Week 1)
    "sympy_reasoning": SymPyReasoningBlock,
    "boq_processor": BOQProcessorBlock,
    "spec_analyzer": SpecAnalyzerBlock,
    # Construction Domain (Week 2)
    "drawing_qto": DrawingQTOBlock,
    "primavera_parser": PrimaveraParserBlock,
    "smart_orchestrator": SmartOrchestratorBlock,
    # Intelligence (Week 3)
    "jetson_gateway": JetsonGatewayBlock,
    "formula_executor": FormulaExecutorBlock,
    "bim_extractor": BIMExtractorBlock,
    # Intelligence (Week 4)
    "learning_engine": LearningEngineBlock,
    "historical_benchmark": HistoricalBenchmarkBlock,
    "recommendation_template": RecommendationTemplateBlock,
    # ML Engine
    "ml_engine": MLEngineBlock,
    # Reasoning Engine Blocks
    "validator": ValidatorBlock,
    "credibility_scorer": CredibilityScorerBlock,
    "predictive_engine": PredictiveEngineBlock,
    "evidence_vault": EvidenceVaultBlock,
    # Telegram Bot
    "telegram_bot": TelegramBotBlock,
    # Infrastructure
    "orchestrator": OrchestratorBlock,
    "traffic_manager": TrafficManagerBlock,
    "event_bus": EventBusBlock,
    "context_broker": ContextBrokerBlock,
    "llm_enhancer": LLMEnhancerBlock,
    "cache_manager": CacheManagerBlock,
    "async_processor": AsyncProcessorBlock,
    "file_hasher": FileHasherBlock,
    # Domain Containers
    "construction": ConstructionContainer,
    "medical": MedicalContainer,
    "legal": LegalContainer,
    "finance": FinanceContainer,
    "security": SecurityContainer,
    "ai_core": AICoreContainer,
    "store": StoreContainer,
    "libraries": LibrariesContainer,
    "ml": MLContainer,
    "reasoning_engine": ReasoningEngineContainer,
}


def get_block(name: str):
    """Get a block class by name"""
    return BLOCK_REGISTRY.get(name)


def get_all_blocks():
    """Get all registered blocks"""
    return BLOCK_REGISTRY


__all__ = [
    # Base
    "UniversalBlock", "UniversalContainer",
    # Core
    "ChatBlock", "PDFBlock", "OCRBlock", "VoiceBlock", "VectorSearchBlock",
    "ImageBlock", "TranslateBlock", "CodeBlock", "WebBlock", "SearchBlock", "ZvecBlock",
    # Drive
    "GoogleDriveBlock", "OneDriveBlock", "LocalDriveBlock", "AndroidDriveBlock",
    # Infrastructure
    "OrchestratorBlock", "TrafficManagerBlock", "EventBusBlock", "ContextBrokerBlock",
    "LLMEnhancerBlock", "CacheManagerBlock", "AsyncProcessorBlock", "FileHasherBlock",
    # Containers
    "ConstructionContainer", "MedicalContainer", "LegalContainer", "FinanceContainer",
    "SecurityContainer", "AICoreContainer", "StoreContainer",
    # Construction Intelligence (all weeks)
    "SymPyReasoningBlock", "BOQProcessorBlock", "SpecAnalyzerBlock",
    "DrawingQTOBlock", "PrimaveraParserBlock", "SmartOrchestratorBlock",
    "JetsonGatewayBlock", "FormulaExecutorBlock", "BIMExtractorBlock",
    "LearningEngineBlock", "HistoricalBenchmarkBlock", "RecommendationTemplateBlock",
    # ML Engine + Containers
    "MLEngineBlock",
    "ValidatorBlock", "CredibilityScorerBlock", "PredictiveEngineBlock", "EvidenceVaultBlock",
    "LibrariesContainer", "MLContainer", "ReasoningEngineContainer",
    # Telegram
    "TelegramBotBlock",
    # Registry
    "BLOCK_REGISTRY", "get_block", "get_all_blocks"
]
