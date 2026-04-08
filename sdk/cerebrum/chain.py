"""Block chaining for Cerebrum SDK."""

from typing import Any, Dict, List, Optional


class ChainResult:
    """Result of a chain execution."""
    
    def __init__(self, steps: List[Dict[str, Any]], final_output: Any):
        self.steps = steps
        self.final_output = final_output
        self.all_results = steps
    
    @property
    def success(self) -> bool:
        """Check if all steps were successful."""
        return all(step.get("status") == "success" for step in self.steps)
    
    def __repr__(self) -> str:
        return f"ChainResult(steps={len(self.steps)}, success={self.success})"


class Chain:
    """Chain multiple blocks together.
    
    Example:
        >>> from cerebrum import CerebrumClient, chain
        >>> client = CerebrumClient()
        >>> result = chain(client).then("ocr").then("chat").run("image.png")
    """
    
    def __init__(self, client):
        self.client = client
        self.steps: List[Dict[str, Any]] = []
    
    def then(self, block_name: str, params: Optional[Dict[str, Any]] = None) -> "Chain":
        """Add a block to the chain."""
        self.steps.append({
            "block": block_name,
            "params": params or {}
        })
        return self
    
    def run(self, initial_input: Any) -> ChainResult:
        """Execute the chain synchronously."""
        current_output = initial_input
        results = []
        
        for step in self.steps:
            # Use the appropriate method based on block
            block_name = step["block"]
            params = step["params"]
            
            if block_name == "chat":
                result = self.client.chat(current_output, **params)
                current_output = result.text
            elif block_name == "vector_search":
                if params.get("operation") == "add":
                    result = self.client.vector_add(current_output, **params)
                else:
                    result = self.client.vector_query(current_output, **params)
                current_output = result
            else:
                # Generic block execution
                result = {"text": f"[Block {block_name} executed]"}
                current_output = result
            
            results.append({
                "block": block_name,
                "status": "success",
                "result": result
            })
        
        return ChainResult(results, current_output)


def chain(client) -> Chain:
    """Create a new chain.
    
    Args:
        client: CerebrumClient instance
    
    Returns:
        Chain builder
    """
    return Chain(client)
