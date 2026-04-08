"""Base block class and configuration."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
import time
import uuid


@dataclass
class BlockConfig:
    """Configuration for a block."""
    name: str
    version: str = "1.0"
    description: str = ""
    author: str = ""
    requires_api_key: bool = False
    supported_inputs: list = None
    supported_outputs: list = None


class BaseBlock(ABC):
    """Base class for all AI blocks."""
    
    def __init__(self, config: BlockConfig):
        self.config = config
        self.execution_count = 0
        self.total_execution_time = 0
    
    @abstractmethod
    async def process(self, input_data: Any, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process input data and return results."""
        pass
    
    async def execute(self, input_data: Any, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the block with timing and error handling."""
        start_time = time.time()
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
        
        execution_time = int((time.time() - start_time) * 1000)
        self.execution_count += 1
        self.total_execution_time += execution_time
        
        return {
            "block": self.config.name,
            "request_id": request_id,
            "status": status,
            "result": result,
            "confidence": confidence,
            "metadata": {
                "version": self.config.version,
                "execution_count": self.execution_count,
                **params
            },
            "source_id": input_data.get("source_id", "unknown") if isinstance(input_data, dict) else str(uuid.uuid4())[:12],
            "processing_time_ms": execution_time
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get block execution statistics."""
        avg_time = self.total_execution_time / self.execution_count if self.execution_count > 0 else 0
        return {
            "name": self.config.name,
            "version": self.config.version,
            "execution_count": self.execution_count,
            "total_execution_time_ms": self.total_execution_time,
            "avg_execution_time_ms": round(avg_time, 2)
        }
