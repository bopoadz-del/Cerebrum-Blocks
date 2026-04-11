"""Base LegoBlock class for Cerebrum Blocks."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import time
import uuid


class LegoBlock(ABC):
    """Base class for all Cerebrum Blocks."""
    
    name = "base"
    version = "1.0.0"
    requires = []
    
    def __init__(self, hal_block=None, config: Optional[Dict] = None):
        self.hal = hal_block
        self.config = config or {}
        self.execution_count = 0
        self.total_execution_time = 0
        self.initialized = False
    
    @abstractmethod
    async def execute(self, input_data: Dict) -> Dict:
        """Execute the block with the given input."""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the block."""
        pass
    
    async def health(self) -> Dict[str, Any]:
        """Return health status."""
        return {
            "name": self.name,
            "version": self.version,
            "initialized": self.initialized,
            "execution_count": self.execution_count,
            "healthy": True
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get block statistics."""
        avg_time = self.total_execution_time / self.execution_count if self.execution_count > 0 else 0
        return {
            "name": self.name,
            "version": self.version,
            "execution_count": self.execution_count,
            "total_execution_time_ms": self.total_execution_time,
            "avg_execution_time_ms": round(avg_time, 2)
        }
