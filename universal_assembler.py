#!/usr/bin/env python3
"""
Universal Assembler - Auto-discovers, sorts, and wires any LegoBlock
Drop a new block folder → it's automatically assembled.
"""

import os
import sys
import importlib
import inspect
import asyncio
from pathlib import Path
from typing import Dict, List, Type, Any, Optional, Set
from collections import defaultdict, deque

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from blocks.hal.src.detector import HALBlock


class UniversalAssembler:
    """Auto-discovers and assembles any LegoBlock implementation"""
    
    # Layer definitions (lower = initialize first)
    LAYERS = {
        0: "infrastructure",  # HAL, Config, Database
        1: "security",        # Memory, Auth
        2: "monitoring",      # Monitoring, Failover
        3: "core",            # Queue, Storage, Vector
        4: "integration",     # Email, Webhook, Search
        5: "ai",              # Chat, Image, Voice
        6: "domain",          # BIM, PDF, OCR
        7: "utility",         # Code, Translate, Zvec
        99: "unassigned"
    }
    
    def __init__(self, blocks_path: str = "blocks", mode: str = "full"):
        self.blocks_path = Path(blocks_path)
        self.mode = mode
        self.hal = HALBlock()
        self.discovered: Dict[str, Type] = {}
        self.instances: Dict[str, Any] = {}
        self.dep_graph: Dict[str, Set[str]] = defaultdict(set)
        
    def discover(self) -> Dict[str, Type]:
        """Auto-discover all LegoBlock classes in blocks/"""
        print(f"🔍 Scanning {self.blocks_path}...")
        
        if not self.blocks_path.exists():
            raise FileNotFoundError(f"Blocks path not found: {self.blocks_path}")
        
        # Add project root to path
        sys.path.insert(0, str(self.blocks_path.parent))
        
        found = {}
        
        for block_dir in sorted(self.blocks_path.iterdir()):
            if not block_dir.is_dir():
                continue
            if block_dir.name.startswith('__'):
                continue
                
            block_name = block_dir.name
            src_file = block_dir / "src" / "block.py"
            
            if not src_file.exists():
                continue
            
            try:
                # Import: blocks.{name}.src.block
                module_path = f"blocks.{block_name}.src.block"
                
                # Clear cache for hot-reload support
                if module_path in sys.modules:
                    del sys.modules[module_path]
                    
                module = importlib.import_module(module_path)
                
                # Find LegoBlock subclasses
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Skip base classes and non-blocks
                    if name == "LegoBlock":
                        continue
                    if hasattr(obj, 'name') and hasattr(obj, 'requires'):
                        instance_name = getattr(obj, 'name', block_name)
                        found[instance_name] = obj
                        print(f"   ✓ {instance_name} ({obj.__name__}) - layer {getattr(obj, 'layer', 99)}")
                        
            except Exception as e:
                print(f"   ⚠️  {block_name}: {e}")
                continue
        
        self.discovered = found
        print(f"\n📦 Discovered {len(found)} blocks")
        return found
    
    def build_deps(self):
        """Build dependency graph from block.requires"""
        for name, block_class in self.discovered.items():
            self.dep_graph[name] = set(getattr(block_class, 'requires', []))
        return self.dep_graph
    
    def topological_sort(self) -> List[str]:
        """Sort blocks by dependencies and layer (Kahn's algorithm)"""
        in_degree = defaultdict(int)
        graph = defaultdict(list)
        
        # Build reverse graph
        for block, deps in self.dep_graph.items():
            in_degree[block]  # Ensure exists
            for dep in deps:
                if dep in self.discovered:  # Only track known deps
                    graph[dep].append(block)
                    in_degree[block] += 1
        
        # Start with no-deps nodes, sorted by layer
        queue = deque(sorted(
            [n for n in self.discovered if in_degree[n] == 0],
            key=lambda x: (getattr(self.discovered[x], 'layer', 99), x)
        ))
        
        sorted_blocks = []
        
        while queue:
            node = queue.popleft()
            sorted_blocks.append(node)
            
            for dependent in graph[node]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
            
            # Re-sort queue by layer for consistent ordering
            queue = deque(sorted(queue, key=lambda x: (
                getattr(self.discovered[x], 'layer', 99), x
            )))
        
        # Check for circular deps
        if len(sorted_blocks) != len(self.discovered):
            missing = set(self.discovered.keys()) - set(sorted_blocks)
            raise ValueError(f"Circular dependency or missing deps: {missing}")
        
        return sorted_blocks
    
    def _build_config(self, name: str, block_class: Type) -> Dict:
        """Build config from env vars and defaults"""
        config = {}
        
        # Class defaults
        if hasattr(block_class, 'default_config'):
            config.update(block_class.default_config)
        
        # Environment: CEREBRUM_{BLOCK}_{KEY}
        prefix = f"CEREBRUM_{name.upper()}_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                config[config_key] = value
        
        return config
    
    async def assemble(self) -> Dict[str, Any]:
        """Main assembly pipeline"""
        profile = self.hal.detect()
        caps = self.hal.get_capabilities()
        
        print(f"\n🔧 Universal Assembler | Mode: {self.mode}")
        print(f"   HAL: {profile.value}")
        print(f"   GPU: {caps.get('has_gpu')}, Memory: {caps.get('memory_gb')}GB")
        
        # 1. Discovery
        self.discover()
        if not self.discovered:
            raise RuntimeError("No blocks discovered!")
        
        # 2. Dependency resolution
        self.build_deps()
        order = self.topological_sort()
        
        print(f"\n📋 Assembly Order:")
        for i, name in enumerate(order, 1):
            deps = self.dep_graph[name]
            dep_str = f" ← {', '.join(deps)}" if deps else ""
            layer = getattr(self.discovered[name], 'layer', 99)
            print(f"   {i}. {name} (L{layer}){dep_str}")
        
        # 3. Instantiation & Wiring
        print(f"\n🔌 Initializing...")
        
        for name in order:
            block_class = self.discovered[name]
            config = self._build_config(name, block_class)
            
            # Instantiate
            instance = block_class(hal_block=self.hal, config=config)
            self.instances[name] = instance
            
            # Auto-wire dependencies via inject()
            for dep_name in self.dep_graph[name]:
                if dep_name in self.instances:
                    if hasattr(instance, 'inject'):
                        instance.inject(dep_name, self.instances[dep_name])
                    else:
                        # Fallback: direct attribute setting
                        setattr(instance, f"{dep_name}_block", self.instances[dep_name])
                    print(f"   🔗 {name} → {dep_name}")
            
            # Initialize
            try:
                success = await instance.initialize()
                status = "✅" if success else "⚠️"
            except Exception as e:
                print(f"   ❌ {name}: {e}")
                success = False
                status = "❌"
            
            print(f"   {status} {name}")
        
        # 4. Health check
        await self._health_check()
        
        return self.instances
    
    async def _health_check(self):
        """Health check all blocks"""
        print(f"\n💚 Health Check:")
        healthy = 0
        for name, instance in self.instances.items():
            try:
                h = instance.health()
                ok = h.get('healthy', False)
                status = "🟢" if ok else "🟡"
                if ok:
                    healthy += 1
                deps = h.get('dependencies', [])
                dep_info = f" [{len(deps)} deps]" if deps else ""
                print(f"   {status} {name}: v{h.get('version', '?')}{dep_info}")
            except Exception as e:
                print(f"   🔴 {name}: {str(e)[:40]}")
        
        print(f"\n✅ Assembled: {len(self.instances)} blocks | Healthy: {healthy}/{len(self.instances)}")
    
    def get(self, name: str) -> Optional[Any]:
        """Get assembled block"""
        return self.instances.get(name)
    
    async def execute(self, block_name: str, input_data: Dict) -> Dict:
        """Execute a block"""
        block = self.get(block_name)
        if not block:
            return {"error": f"Block '{block_name}' not found"}
        return await block.execute(input_data)


async def main():
    """CLI test"""
    print("="*60)
    print("🔥 UNIVERSAL ASSEMBLER")
    print("="*60)
    
    assembler = UniversalAssembler(mode="full")
    blocks = await assembler.assemble()
    
    # Quick test
    if 'memory' in blocks:
        print(f"\n🧪 Testing Memory block...")
        result = await assembler.execute('memory', {'action': 'stats'})
        print(f"   Cache stats: {result}")
    
    if 'search' in blocks:
        print(f"\n🧪 Testing Search block...")
        result = await assembler.execute('search', {'action': 'search', 'query': 'test', 'provider': 'duckduckgo'})
        print(f"   Results: {result.get('count', 0)} found")


if __name__ == "__main__":
    asyncio.run(main())
