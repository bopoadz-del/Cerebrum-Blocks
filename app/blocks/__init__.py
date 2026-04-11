"""Platform Branch - Core + Platform + Store Containers."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Try Universal Assembler
try:
    from universal_assembler import UniversalAssembler
    ASSEMBLER = UniversalAssembler(mode="platform")  # Platform mode
    DISCOVERED = ASSEMBLER.discover()
    
    # Filter for platform-relevant blocks
    PLATFORM_BLOCKS = {k: v for k, v in DISCOVERED.items() 
                      if not k.startswith('container_') or k in [
                          'container_platform', 'container_store', 'event_bus'
                      ]}
    
    BLOCK_REGISTRY = PLATFORM_BLOCKS
    
except Exception as e:
    # Fallback to manual registration
    print(f"Warning: Using fallback registration: {e}")
    
    # Core blocks
    from app.blocks.pdf import PDFBlock
    from app.blocks.ocr import OCRBlock
    from app.blocks.chat import ChatBlock
    
    BLOCK_REGISTRY = {
        "pdf": PDFBlock,
        "ocr": OCRBlock,
        "chat": ChatBlock,
    }

def get_block(name: str):
    return BLOCK_REGISTRY.get(name)

def get_all_blocks():
    return BLOCK_REGISTRY
