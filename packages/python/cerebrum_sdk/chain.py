"""Chain builder for composing blocks."""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Cerebrum


class Chain:
    """Builder for chaining multiple blocks together.
    
    Chain blocks to create powerful AI pipelines:
    PDF → OCR → Chat = Document AI in 3 lines
    
    Example:
        >>> from cerebrum_sdk import Cerebrum, chain
        >>> 
        >>> client = Cerebrum(api_key="cb_your_key")
        >>> 
        >>> result = await chain(client) \
        ...     .then("pdf", {"extract": "text"}) \
        ...     .then("translate", {"target": "en"}) \
        ...     .then("chat", {"prompt": "Summarize:"}) \
        ...     .run("document.pdf")
        >>> 
        >>> print(result.final_output)
    """
    
    def __init__(self, client: "Cerebrum"):
        self.client = client
        self.steps: List[Dict[str, Any]] = []
    
    def then(self, block: str, params: Optional[Dict[str, Any]] = None) -> "Chain":
        """Add a block to the chain.
        
        Args:
            block: Block name (chat, pdf, ocr, translate, etc.)
            params: Parameters for this block
        
        Returns:
            Self for method chaining
        
        Example:
            >>> chain.then("pdf", {"extract": "text"})
            >>> chain.then("chat", {"prompt": "Summarize:"})
        """
        self.steps.append({
            "block": block,
            "params": params or {}
        })
        return self
    
    async def run(self, initial_input: Any) -> "ChainResult":
        """Execute the chain with initial input.
        
        Args:
            initial_input: Starting input (file path, text, etc.)
        
        Returns:
            ChainResult with final_output and step_results
        """
        result = await self.client.chain(self.steps, initial_input)
        return ChainResult(result)


class ChainResult:
    """Result of a chain execution.
    
    Attributes:
        success: Whether all steps completed successfully
        final_output: The final output from the chain
        steps_executed: Number of steps that ran
        total_time_ms: Total execution time in milliseconds
        step_results: Detailed results from each step
    """
    
    def __init__(self, data: Dict[str, Any]):
        self._data = data
    
    @property
    def success(self) -> bool:
        """Whether all steps completed successfully."""
        return self._data.get("status") == "success"
    
    @property
    def final_output(self) -> Any:
        """The final output from the chain."""
        return self._data.get("final_output")
    
    @property
    def steps_executed(self) -> int:
        """Number of steps that ran."""
        return self._data.get("steps_executed", 0)
    
    @property
    def total_time_ms(self) -> int:
        """Total execution time in milliseconds."""
        return self._data.get("total_time_ms", 0)
    
    @property
    def step_results(self) -> List[Dict[str, Any]]:
        """Detailed results from each step."""
        return self._data.get("step_results", [])
    
    @property
    def raw(self) -> Dict[str, Any]:
        """Raw response data."""
        return self._data
    
    def __repr__(self) -> str:
        return f"ChainResult(success={self.success}, steps={self.steps_executed})"


def chain(client: "Cerebrum") -> Chain:
    """Create a new chain builder.
    
    Args:
        client: Cerebrum client instance
    
    Returns:
        Chain builder for composing blocks
    
    Example:
        >>> from cerebrum_sdk import Cerebrum, chain
        >>> client = Cerebrum(api_key="cb_your_key")
        >>> 
        >>> result = await chain(client) \
        ...     .then("pdf", {"extract": "text"}) \
        ...     .then("chat", {"prompt": "Summarize:"}) \
        ...     .run("document.pdf")
    """
    return Chain(client)
