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

# Document Engine
from .document_engine import DocumentEngineBlock

# Construction Intelligence Blocks
from .historical_benchmark import HistoricalBenchmarkBlock

# Containers
from app.containers import ConstructionContainer

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
    
    # Document Engine
    "document_engine": DocumentEngineBlock,

    # Construction Intelligence Blocks
    "historical_benchmark": HistoricalBenchmarkBlock,

    # Containers
    "construction": ConstructionContainer,
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
