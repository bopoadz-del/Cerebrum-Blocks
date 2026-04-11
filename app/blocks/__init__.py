"""Cerebrum Blocks - Lazy loading for memory efficiency (Starter Plan)."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Lazy registry - only load what's needed
_block_cache = {}
_block_registry = None

def _get_registry():
    """Lazy load the registry"""
    global _block_registry
    if _block_registry is None:
        try:
            from universal_assembler import UniversalAssembler
            _assembler = UniversalAssembler(mode="production")
            _block_registry = _assembler.discover()
            print(f"✅ Discovered {len(_block_registry)} blocks")
        except Exception as e:
            print(f"⚠️  Discovery failed: {e}")
            _block_registry = {}
    return _block_registry

def get_block(name: str):
    """Get a block class (lazy load instance)"""
    registry = _get_registry()
    return registry.get(name)

def get_all_blocks():
    """Get all registered block names"""
    return _get_registry()

# Core blocks for immediate use
CORE_BLOCKS = [
    "pdf", "ocr", "chat", "voice", "image", "vector_search", 
    "search", "translate", "code", "web", "zvec"
]

__all__ = ["get_block", "get_all_blocks", "CORE_BLOCKS"]
