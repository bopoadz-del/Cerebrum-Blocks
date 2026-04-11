"""Full Cerebrum Blocks - All 58 blocks + containers (Upgraded Plan)."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import Universal Assembler
try:
    from universal_assembler import UniversalAssembler
    
    # Initialize and discover all blocks
    _assembler = UniversalAssembler(mode="production")
    BLOCK_REGISTRY = _assembler.discover()
    
    print(f"✅ Loaded {len(BLOCK_REGISTRY)} blocks/containers")
    
except Exception as e:
    print(f"⚠️  Universal Assembler failed: {e}")
    print(f"🔄 Falling back to manual registration...")
    
    # Legacy imports
    from .pdf import PDFBlock
    from .ocr import OCRBlock
    from .chat import ChatBlock
    
    BLOCK_REGISTRY = {
        "pdf": PDFBlock,
        "ocr": OCRBlock,
        "chat": ChatBlock,
    }

# Helper functions
def register_block(name: str, block_class):
    BLOCK_REGISTRY[name] = block_class

def get_block(name: str):
    return BLOCK_REGISTRY.get(name)

def get_all_blocks():
    return BLOCK_REGISTRY

__all__ = ["BLOCK_REGISTRY", "get_block", "get_all_blocks", "register_block"]
