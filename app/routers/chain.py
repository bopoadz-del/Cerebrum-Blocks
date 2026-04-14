from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.blocks import BLOCK_REGISTRY
from app.core.auth import require_api_key
from app.dependencies import block_instances, _create_block_instance

router = APIRouter()


class ChainRequest(BaseModel):
    steps: List[Dict[str, Any]] = Field(..., description="Chain of blocks to execute")
    initial_input: Optional[Any] = Field(default=None, description="Starting input")


@router.post("/chain")
async def chain_execute(request: ChainRequest, auth: dict = Depends(require_api_key)):
    """Execute a chain of blocks via OrchestratorBlock."""
    if "orchestrator" not in BLOCK_REGISTRY:
        raise HTTPException(500, "Orchestrator block not available")

    try:
        if "orchestrator" not in block_instances:
            block_instances["orchestrator"] = _create_block_instance(BLOCK_REGISTRY["orchestrator"])

        orchestrator = block_instances["orchestrator"]
        orch_result = await orchestrator.execute(
            request.initial_input,
            {"steps": request.steps}
        )

        inner = orch_result.get("result", {})

        return {
            "success": inner.get("status") == "success",
            "steps_executed": inner.get("steps_executed", 0),
            "final_output": inner.get("final_output"),
            "results": inner.get("results", []),
        }

    except Exception as e:
        raise HTTPException(500, f"Chain execution failed: {str(e)}")


@router.post("/v1/chain")
async def chain_execute_v1(request: ChainRequest, auth: dict = Depends(require_api_key)):
    """Execute a chain of blocks (v1 API)."""
    return await chain_execute(request)
