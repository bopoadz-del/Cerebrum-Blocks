"""Enterprise Branch - Full 58 blocks + 8 containers + Event Bus."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Full Universal Assembler
try:
    from universal_assembler import UniversalAssembler
    ASSEMBLER = UniversalAssembler(mode="production")
    BLOCK_REGISTRY = ASSEMBLER.discover()
    print(f"✅ Enterprise: {len(BLOCK_REGISTRY)} blocks loaded")
except Exception as e:
    print(f"❌ Discovery failed: {e}")
    BLOCK_REGISTRY = {}

def get_block(name: str):
    return BLOCK_REGISTRY.get(name)

def get_all_blocks():
    return BLOCK_REGISTRY

def discover_all():
    """Rediscover all blocks"""
    global BLOCK_REGISTRY
    if 'ASSEMBLER' in globals():
        BLOCK_REGISTRY = ASSEMBLER.discover()
    return BLOCK_REGISTRY
