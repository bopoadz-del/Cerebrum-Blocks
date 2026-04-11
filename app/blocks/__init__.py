"""All AI and Drive blocks - Now with Universal Assembler integration."""

import sys
import os
from typing import Dict, Any, Optional

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Try to import from Universal Assembler
try:
    from universal_assembler import UniversalAssembler
    ASSEMBLER_AVAILABLE = True
except ImportError:
    ASSEMBLER_AVAILABLE = False

# Legacy imports for backwards compatibility
from .pdf import PDFBlock
from .ocr import OCRBlock
from .chat import ChatBlock
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

__all__ = [
    # AI Blocks
    "PDFBlock",
    "OCRBlock",
    "ChatBlock",
    "VoiceBlock",
    "VectorSearchBlock",
    "ImageBlock",
    "TranslateBlock",
    "CodeBlock",
    "WebBlock",
    "SearchBlock",
    "ZvecBlock",
    # Drive Blocks
    "GoogleDriveBlock",
    "OneDriveBlock",
    "LocalDriveBlock",
    "AndroidDriveBlock",
    # New
    "BLOCK_REGISTRY",
    "get_block",
    "get_all_blocks",
    "discover_all_blocks",
]

BLOCK_REGISTRY: Dict[str, Any] = {}
_assembler_instance: Optional[UniversalAssembler] = None

def _init_legacy_registry():
    """Initialize legacy block registry"""
    global BLOCK_REGISTRY
    BLOCK_REGISTRY = {
        "pdf": PDFBlock,
        "ocr": OCRBlock,
        "chat": ChatBlock,
        "voice": VoiceBlock,
        "vector_search": VectorSearchBlock,
        "image": ImageBlock,
        "translate": TranslateBlock,
        "code": CodeBlock,
        "web": WebBlock,
        "search": SearchBlock,
        "zvec": ZvecBlock,
        "google_drive": GoogleDriveBlock,
        "onedrive": OneDriveBlock,
        "local_drive": LocalDriveBlock,
        "android_drive": AndroidDriveBlock,
    }

def discover_all_blocks() -> Dict[str, Any]:
    """Discover all blocks using Universal Assembler"""
    global BLOCK_REGISTRY, _assembler_instance
    
    if not ASSEMBLER_AVAILABLE:
        _init_legacy_registry()
        return BLOCK_REGISTRY
    
    try:
        # Use Universal Assembler to discover
        _assembler_instance = UniversalAssembler(mode="production")
        discovered = _assembler_instance.discover()
        
        # Merge with legacy registry (legacy takes precedence for compatibility)
        _init_legacy_registry()
        
        # Add newly discovered blocks
        for name, block_class in discovered.items():
            if name not in BLOCK_REGISTRY:
                BLOCK_REGISTRY[name] = block_class
                
        return BLOCK_REGISTRY
        
    except Exception as e:
        print(f"Warning: Universal Assembler discovery failed: {e}")
        _init_legacy_registry()
        return BLOCK_REGISTRY

def register_block(name: str, block_class):
    """Register a block class."""
    BLOCK_REGISTRY[name] = block_class

def get_block(name: str):
    """Get a block class by name."""
    return BLOCK_REGISTRY.get(name)

def get_all_blocks():
    """Get all registered blocks."""
    if not BLOCK_REGISTRY:
        discover_all_blocks()
    return BLOCK_REGISTRY

# Initialize on import
discover_all_blocks()
