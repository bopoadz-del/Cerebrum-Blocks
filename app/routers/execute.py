import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.blocks import BLOCK_REGISTRY
from app.dependencies import require_api_key
from app.dependencies import block_instances, _create_block_instance
from app.core.input_adapter import adapt_input
from app.core.security import enforce_block_access

logger = logging.getLogger(__name__)
router = APIRouter()


class ExecuteRequest(BaseModel):
    block: str = Field(..., description="Block name (chat, pdf, ocr, voice, etc.)")
    input: Optional[Any] = Field(default=None, description="Input data for the block")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Block parameters")


@router.post("/execute")
async def execute(request: ExecuteRequest, auth: dict = Depends(require_api_key)):
    """Execute a single block."""
    block_name = request.block

    if block_name not in BLOCK_REGISTRY:
        raise HTTPException(404, f"Block '{block_name}' not found. Available: {list(BLOCK_REGISTRY.keys())}")

    # Skip containers - they belong to Block Store
    if block_name.startswith("container_"):
        raise HTTPException(400, f"Container '{block_name}' cannot be executed directly. Use Block Store.")

    # Tier × block guard — RCE / SSRF / vault / FS blocks are restricted
    # to unlimited-tier keys. Standard-tier (including the SPA-shipped
    # public key) gets 403 here instead of being allowed to invoke the
    # block and rely on the block's own (often missing) sandbox.
    enforce_block_access(block_name, auth)

    try:
        if block_name not in block_instances:
            block_instances[block_name] = _create_block_instance(BLOCK_REGISTRY[block_name])

        block = block_instances[block_name]
        
        # Adapt input to what block expects
        adapted_input = adapt_input(request.input, block)
        
        result = await block.execute(adapted_input, request.params or {})
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("block execution failed", extra={"block": block_name})
        # Distinguish "operator config missing / network down" (503) from
        # "real internal failure" (500) so SPAs and downstream services
        # can decide whether to retry, fall back, or surface a setup error.
        from app.core.http_errors import classify_block_error
        err = f"Execution failed: {e}"
        status = classify_block_error(str(e))
        # 422 isn't right for an unhandled exception — bump to 500 for those.
        if status == 422:
            status = 500
        raise HTTPException(status, err)


@router.post("/v1/execute")
async def execute_v1(request: ExecuteRequest, auth: dict = Depends(require_api_key)):
    """Execute a single block (v1 API)."""
    # Re-check the block access here too — execute() called as a coroutine
    # below doesn't run FastAPI dependencies, so the auth dict from this
    # handler is what we need to gate against.
    if request.block in BLOCK_REGISTRY:
        enforce_block_access(request.block, auth)
    return await execute(request)
