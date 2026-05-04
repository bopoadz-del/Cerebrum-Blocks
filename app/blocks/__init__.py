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

# ── File Access ───────────────────────────────────────────────────────────────
from .local_drive import LocalDriveBlock
from .google_drive import GoogleDriveBlock
from .onedrive import OneDriveBlock

# ── Search & Memory ───────────────────────────────────────────────────────────
from .vector_search import VectorSearchBlock
from .zvec import ZvecBlock
from .cache_manager import CacheManagerBlock

# Construction Domain Blocks (Week 2)
from .drawing_qto import DrawingQTOBlock
from .primavera_parser import PrimaveraParserBlock
from .smart_orchestrator import SmartOrchestratorBlock
from .skills import SkillsBlock


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
    "skills": SkillsBlock,
    # Intelligence (Week 3)
    "jetson_gateway": JetsonGatewayBlock,
    "formula_executor": FormulaExecutorBlock,
    "bim_extractor": BIMExtractorBlock,
    # Intelligence (Week 4)
    "learning_engine": LearningEngineBlock,
    "historical_benchmark": HistoricalBenchmarkBlock,
    "smart_orchestrator":   SmartOrchestratorBlock,

    # File Access
    "local_drive":      LocalDriveBlock,
    "google_drive":     GoogleDriveBlock,
    "onedrive":         OneDriveBlock,

    # Search & Memory
    "vector_search":    VectorSearchBlock,
    "zvec":             ZvecBlock,
    "cache_manager":    CacheManagerBlock,
}


def get_block(name: str):
    return BLOCK_REGISTRY.get(name)


def get_all_blocks():
    return BLOCK_REGISTRY


__all__ = [
    # Base classes
    "UniversalBlock", "UniversalContainer", "TypedBlock",
    
    # Core v1
    "ChatBlock", "PDFBlock", "OCRBlock", "VoiceBlock", "VectorSearchBlock",
    "ImageBlock", "TranslateBlock", "CodeBlock", "WebBlock", "SearchBlock", "ZvecBlock",
    
    # Core v2
    "PDFBlockV2", "OCRBlockV2", "ConstructionBlockV2",
    
    # Drive
    "GoogleDriveBlock", "OneDriveBlock", "LocalDriveBlock", "AndroidDriveBlock",
    
    # Infrastructure
    "OrchestratorBlock", "TrafficManagerBlock", "EventBusBlock", "ContextBrokerBlock",
    "LLMEnhancerBlock", "CacheManagerBlock", "AsyncProcessorBlock", "FileHasherBlock",
    
    # Containers v1
    "ConstructionContainer", "MedicalContainer", "LegalContainer", "FinanceContainer",
    "SecurityContainer", "AICoreContainer", "StoreContainer",
    # Construction Intelligence (all weeks)
    "SymPyReasoningBlock", "BOQProcessorBlock", "SpecAnalyzerBlock",
    "DrawingQTOBlock", "PrimaveraParserBlock", "SmartOrchestratorBlock",
    "SkillsBlock",
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
