#!/usr/bin/env python3
"""
BLOCK STORE - The Cerebrum Marketplace

This is the block publishing and discovery system.
Separate from the Platform - this is where blocks are:
- Published by creators
- Discovered by users  
- Validated and reviewed
- Versioned and distributed

Run: python blockstore.py
"""

import asyncio
from universal_assembler import UniversalAssembler

async def main():
    print("="*60)
    print("🏪 CEREBRUM BLOCK STORE")
    print("="*60)
    
    # Load ALL blocks from blocks/ directory
    assembler = UniversalAssembler(mode="production")
    blocks = assembler.discover()
    
    print(f"\n📦 Total blocks in store: {len(blocks)}")
    print("\n🏷️  By Category:")
    
    # Categorize
    categories = {
        "Containers": [],
        "AI/Core": [],
        "Security": [],
        "Storage": [],
        "Utilities": []
    }
    
    for name, block_class in blocks.items():
        if name.startswith("container_"):
            categories["Containers"].append(name)
        elif name in ["chat", "vector_search", "adaptive_router", "failover"]:
            categories["AI/Core"].append(name)
        elif name in ["auth", "secrets", "sandbox", "audit", "rate_limiter"]:
            categories["Security"].append(name)
        elif name in ["storage", "database", "memory"]:
            categories["Storage"].append(name)
        else:
            categories["Utilities"].append(name)
    
    for cat, items in categories.items():
        if items:
            print(f"\n  {cat}: {len(items)}")
            for item in items[:5]:
                print(f"    - {item}")
            if len(items) > 5:
                print(f"    ... and {len(items)-5} more")
    
    print("\n✅ Block Store ready for publishing!")

if __name__ == "__main__":
    asyncio.run(main())
