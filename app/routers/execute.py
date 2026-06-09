import json
import logging
import subprocess
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.blocks import BLOCK_REGISTRY
from app.dependencies import require_api_key
from app.dependencies import block_instances, _create_block_instance
from app.core.input_adapter import adapt_input
from app.core.security import enforce_block_access
from app.block_registry import registry_block_exists

logger = logging.getLogger(__name__)
router = APIRouter()


def _run_registry_block(block_name: str, input_data: Any, params: Dict) -> dict:
    """Execute a block via its registry adapter using subprocess.
    
    Reads JSON from stdin, parses JSON stdout.
    Falls back to error dict if subprocess fails.
    """
    import os
    registry_dir = os.path.join(os.path.dirname(__file__), "..", "..", "block_registry", block_name)
    adapter_path = os.path.join(registry_dir, "block.py")
    
    if not os.path.exists(adapter_path):
        return {"success": False, "error": f"Registry adapter not found for {block_name}"}
    
    # Build stdin payload
    payload = {"input": input_data}
    if params:
        payload.update(params)
    
    try:
        proc = subprocess.run(
            ["python", adapter_path],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=60,
            cwd=os.path.join(os.path.dirname(__file__), "..", ".."),
        )
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Block {block_name} timed out after 60s"}
    except Exception as e:
        return {"success": False, "error": f"Failed to run block {block_name}: {e}"}
    
    if proc.returncode != 0:
        return {"success": False, "error": proc.stderr or f"Block {block_name} exited with code {proc.returncode}"}
    
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"success": False, "error": f"Invalid JSON output from block {block_name}", "raw_output": proc.stdout}
    
    return result


class ExecuteRequest(BaseModel):
    block: str = Field(..., description="Block name (chat, pdf, ocr, voice, etc.)")
    input: Optional[Any] = Field(default=None, description="Input data for the block")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Block parameters")


async def _run_block(request: ExecuteRequest, auth: dict) -> dict:
    """Shared body for /execute and /v1/execute.

    Both routers do FastAPI auth themselves (Depends(require_api_key))
    and pass the resolved auth dict in. Previously /v1/execute called
    /execute as a coroutine, leaving execute()'s `auth` param at its
    default — the Depends sentinel — which then crashed
    enforce_block_access (`'Depends' object has no attribute 'get'`).
    
    Now also supports registry blocks via subprocess execution.
    """
    block_name = request.block

    # Check registry first (new plug-and-play path)
    if registry_block_exists(block_name):
        enforce_block_access(block_name, auth)
        registry_result = _run_registry_block(block_name, request.input, request.params or {})
        
        if registry_result.get("success"):
            # Wrap in standard envelope for backward compatibility
            return {
                "block": block_name,
                "request_id": "registry",
                "status": "success",
                "result": registry_result.get("output", {}),
                "confidence": 1.0,
                "source_id": f"{block_name}-registry",
                "metadata": {"source": "registry"},
                "processing_time_ms": 0,
            }
        else:
            raise HTTPException(500, registry_result.get("error", "Registry execution failed"))

    # Fall back to inline execution (original path)
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


@router.post("/execute")
async def execute(request: ExecuteRequest, auth: dict = Depends(require_api_key)):
    """Execute a single block."""
    return await _run_block(request, auth)


@router.post("/v1/execute")
async def execute_v1(request: ExecuteRequest, auth: dict = Depends(require_api_key)):
    """Execute a single block (v1 API)."""
    return await _run_block(request, auth)
