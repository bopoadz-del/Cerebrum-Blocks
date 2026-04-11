"""
Universal Block Base Class - The ONE True Block Pattern

All blocks inherit from this. No more dual systems.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import time
import uuid


class UniversalBlock(ABC):
    """
    Universal Block Base Class - Domain Adapter Protocol
    
    All blocks MUST define:
    - name: str - Block identifier
    - version: str - Semver
    - layer: int - Init order (0=infrastructure → 5=interface)
    - tags: List[str] - Categorization
    - requires: List[str] - Dependencies (other block names)
    """
    
    # REQUIRED - define in subclass
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    layer: int = 3  # Default: domain layer
    tags: List[str] = []
    requires: List[str] = []
    
    # Optional
    default_config: Dict = {}
    author: str = ""
    
    def __init__(self, hal_block=None, config: Dict = None):
        """Initialize with HAL and config"""
        self.hal = hal_block
        self.config = {**self.default_config, **(config or {})}
        
        # Execution stats
        self.execution_count = 0
        self.total_execution_time = 0
        
        # Wired dependencies (filled by assembler)
        self._dependencies: Dict[str, Any] = {}
    
    def wire(self, dep_name: str, dep_instance):
        """Wire a dependency (called by assembler)"""
        self._dependencies[dep_name] = dep_instance
    
    def get_dep(self, name: str) -> Optional[Any]:
        """Get a wired dependency"""
        return self._dependencies.get(name)
    
    @abstractmethod
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Main processing - implement in subclass"""
        pass
    
    async def execute(self, input_data: Any, params: Dict = None) -> Dict:
        """Execute with timing and error handling"""
        start = time.time()
        request_id = str(uuid.uuid4())[:12]
        params = params or {}
        
        try:
            result = await self.process(input_data, params)
            status = "success"
            confidence = result.get("confidence", 0.95)
        except Exception as e:
            result = {"error": str(e)}
            status = "error"
            confidence = 0.0
        
        execution_time = int((time.time() - start) * 1000)
        self.execution_count += 1
        self.total_execution_time += execution_time
        
        return {
            "block": self.name,
            "request_id": request_id,
            "status": status,
            "result": result,
            "confidence": confidence,
            "metadata": {
                "version": self.version,
                "execution_count": self.execution_count,
                **params
            },
            "processing_time_ms": execution_time
        }
    
    def get_stats(self) -> Dict:
        """Get execution statistics"""
        avg_time = self.total_execution_time / max(self.execution_count, 1)
        return {
            "name": self.name,
            "version": self.version,
            "layer": self.layer,
            "tags": self.tags,
            "execution_count": self.execution_count,
            "avg_execution_time_ms": round(avg_time, 2)
        }


class UniversalContainer(UniversalBlock):
    """
    Universal Container - Multi-block domain system
    
    Containers group related blocks (e.g., all Construction blocks)
    """
    
    # Containers are always layer 3 (domain)
    layer: int = 3
    tags: List[str] = ["container"]
    
    # Sub-blocks this container provides
    sub_blocks: List[str] = []
    
    async def route(self, action: str, input_data: Any, params: Dict) -> Dict:
        """Route to internal action - override in subclass"""
        raise NotImplementedError(f"Action '{action}' not implemented")
    
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Default: route by action param"""
        params = params or {}
        action = params.get("action", "status")
        return await self.route(action, input_data, params)
