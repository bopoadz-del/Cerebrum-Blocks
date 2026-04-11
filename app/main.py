"""Cerebrum Blocks - Simple Block Execution API."""

import logging
import os
import sys
import time
import json
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Import blocks
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.blocks import BLOCK_REGISTRY, get_all_blocks

# Import HAL for container initialization
try:
    from blocks.hal.src.detector import HALBlock
    _hal = HALBlock()
except Exception as e:
    logger.warning("HALBlock not available during startup: %s", e)
    _hal = None


def _get_cors_origins() -> List[str]:
    """Resolve CORS origins from environment with explicit defaults."""
    raw_origins = os.getenv("CORS_ORIGINS", "").strip()
    
    # Allow all origins for now - restricts via API key
    return ["*"]

def _create_block_instance(block_class):
    """Create block instance with proper arguments"""
    import inspect
    sig = inspect.signature(block_class.__init__)
    params = list(sig.parameters.keys())
    
    # Check if it's a ContainerBlock (needs hal_block, config)
    if 'hal_block' in params and 'config' in params:
        return block_class(hal_block=_hal, config={})
    else:
        # Regular BaseBlock
        return block_class()

app = FastAPI(
    title="Cerebrum Blocks",
    description="Build AI Like Lego - Simple Block Execution API",
    version="2.0.0",
    docs_url="/docs",
)

CORS_ORIGINS = _get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,  # Must be False when using ["*"]
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Store block instances
block_instances: Dict[str, Any] = {}
DATA_DIR = os.getenv("DATA_DIR", "./data")
os.makedirs(DATA_DIR, exist_ok=True)


# -------------------- MODELS --------------------

class ExecuteRequest(BaseModel):
    block: str = Field(..., description="Block name (chat, pdf, ocr, voice, etc.)")
    input: Any = Field(..., description="Input data for the block")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Block parameters")


class ChainRequest(BaseModel):
    steps: List[Dict[str, Any]] = Field(..., description="Chain of blocks to execute")
    initial_input: Any = Field(..., description="Starting input")


class ChatRequest(BaseModel):
    message: str
    model: str = "deepseek-chat"
    stream: bool = False


# -------------------- BLOCKS --------------------

@app.get("/", response_class=FileResponse)
async def root():
    """Serve Block Store UI."""
    return FileResponse("app/static/index.html")


@app.get("/landing", response_class=FileResponse)
async def landing():
    """Serve legacy landing page."""
    return FileResponse("app/static/landing/index.html")


@app.get("/api")
def api_info():
    """API info."""
    return {
        "name": "Cerebrum Blocks",
        "version": "2.0.0",
        "tagline": "Build AI Like Lego",
        "blocks": len(BLOCK_REGISTRY),
        "endpoints": {
            "blocks": "/v1/blocks",
            "execute": "/v1/execute",
            "chain": "/v1/chain",
            "chat": "/v1/chat",
            "health": "/v1/health",
        }
    }


@app.get("/health")
def health():
    """Health check."""
    return {
        "status": "healthy",
        "blocks_loaded": len(block_instances),
        "blocks_available": len(BLOCK_REGISTRY),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/v1/health")
def health_v1():
    """Health check for Render (v1 API)."""
    return {
        "status": "healthy",
        "blocks_loaded": len(block_instances),
        "blocks_available": len(BLOCK_REGISTRY),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/blocks")
def list_blocks():
    """List all available blocks."""
    blocks = []
    for name, block_class in get_all_blocks().items():
        # Skip containers - they belong to Block Store
        if name.startswith("container_"):
            continue
        try:
            if name not in block_instances:
                block_instances[name] = _create_block_instance(block_class)
            instance = block_instances[name]
            
            blocks.append({
                "name": name,
                "version": getattr(instance, 'version', '1.0'),
                "description": getattr(instance, 'description', ''),
                "layer": getattr(instance, 'layer', 3),
                "tags": getattr(instance, 'tags', []),
                "requires": getattr(instance, 'requires', []),
                "ui_schema": getattr(block_class, 'ui_schema', {}),
            })
        except Exception as e:
            blocks.append({
                "name": name,
                "error": str(e),
                "status": "failed"
            })
    
    return {
        "blocks": blocks,
        "total": len(blocks),
        "categories": {
            "ai": ["chat", "pdf", "ocr", "voice", "image", "translate", "code", "web", "search"],
            "storage": ["google_drive", "onedrive", "local_drive", "android_drive"],
        }
    }


@app.get("/blocks/{block_name}")
def get_block_info(block_name: str):
    """Get block details."""
    if block_name not in BLOCK_REGISTRY:
        raise HTTPException(404, f"Block '{block_name}' not found")
    
    if block_name not in block_instances:
        block_instances[block_name] = _create_block_instance(BLOCK_REGISTRY[block_name])
    
    instance = block_instances[block_name]
    block_class = BLOCK_REGISTRY[block_name]
    
    return {
        "name": block_name,
        "config": {
            "version": getattr(instance, 'version', '1.0'),
            "description": getattr(instance, 'description', ''),
            "layer": getattr(instance, 'layer', 3),
            "tags": getattr(instance, 'tags', []),
            "requires": getattr(instance, 'requires', []),
        },
        "ui_schema": getattr(block_class, 'ui_schema', {}),
        "stats": instance.get_stats()
    }


# -------------------- EXECUTE --------------------

@app.post("/execute")
async def execute(request: ExecuteRequest):
    """Execute a single block."""
    block_name = request.block
    
    if block_name not in BLOCK_REGISTRY:
        raise HTTPException(404, f"Block '{block_name}' not found. Available: {list(BLOCK_REGISTRY.keys())}")
    
    # Skip containers - they belong to Block Store
    if block_name.startswith("container_"):
        raise HTTPException(400, f"Container '{block_name}' cannot be executed directly. Use Block Store.")
    
    try:
        if block_name not in block_instances:
            block_instances[block_name] = _create_block_instance(BLOCK_REGISTRY[block_name])
        
        block = block_instances[block_name]
        result = await block.execute(request.input, request.params or {})
        return result
    
    except Exception as e:
        raise HTTPException(500, f"Execution failed: {str(e)}")


# -------------------- CHAIN --------------------

@app.post("/chain")
async def chain_execute(request: ChainRequest):
    """Execute a chain of blocks."""
    results = []
    current_input = request.initial_input
    
    for i, step in enumerate(request.steps):
        block_name = step.get("block")
        params = step.get("params", {})
        
        if block_name not in BLOCK_REGISTRY:
            raise HTTPException(404, f"Step {i}: Block '{block_name}' not found")
        
        # Skip containers
        if block_name.startswith("container_"):
            raise HTTPException(400, f"Step {i}: Container '{block_name}' cannot be executed directly")
        
        try:
            if block_name not in block_instances:
                block_instances[block_name] = _create_block_instance(BLOCK_REGISTRY[block_name])
            
            block = block_instances[block_name]
            result = await block.execute(current_input, params)
            
            results.append({
                "step": i,
                "block": block_name,
                "success": True,
                "result": result
            })
            
            # Pass output to next step
            current_input = result.get("result", result)
            
        except Exception as e:
            results.append({
                "step": i,
                "block": block_name,
                "success": False,
                "error": str(e)
            })
            break
    
    return {
        "success": all(r.get("success") for r in results),
        "steps_executed": len(results),
        "final_output": current_input,
        "results": results
    }


# -------------------- CHAT --------------------

@app.post("/chat")
async def chat(request: ChatRequest):
    """Simple chat endpoint."""
    if "chat" not in BLOCK_REGISTRY:
        raise HTTPException(500, "Chat block not available")
    
    try:
        if "chat" not in block_instances:
            block_instances["chat"] = BLOCK_REGISTRY["chat"]()
        
        block = block_instances["chat"]
        result = await block.execute(request.message, {
            "model": request.model,
            "stream": False,
        })
        
        return {
            "text": result.get("result", {}).get("text", ""),
            "model": request.model,
        }
    
    except Exception as e:
        raise HTTPException(500, f"Chat failed: {str(e)}")


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint."""
    if "chat" not in BLOCK_REGISTRY:
        raise HTTPException(500, "Chat block not available")
    
    async def event_stream():
        try:
            if "chat" not in block_instances:
                block_instances["chat"] = BLOCK_REGISTRY["chat"]()
            
            block = block_instances["chat"]
            result = await block.execute(request.message, {
                "model": request.model,
                "stream": True,
            })
            
            # Get stream generator
            stream_gen = result.get("result", {}).get("stream")
            if stream_gen:
                async for chunk in stream_gen:
                    yield f"data: {json.dumps(chunk)}\n\n"
            else:
                # Fallback: simulate streaming
                text = result.get("result", {}).get("text", "")
                words = text.split()
                for word in words:
                    yield f"data: {json.dumps({'content': word + ' ', 'done': False})}\n\n"
                    await asyncio.sleep(0.05)
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# -------------------- V1 API ROUTES --------------------

@app.get("/v1/blocks")
def list_blocks_v1():
    """List all available blocks (v1 API)."""
    return list_blocks()


@app.get("/v1/blocks/{block_name}")
def get_block_v1(block_name: str):
    """Get block details (v1 API)."""
    return get_block_info(block_name)


@app.post("/v1/execute")
async def execute_v1(request: ExecuteRequest):
    """Execute a single block (v1 API)."""
    return await execute(request)


@app.post("/v1/chain")
async def chain_execute_v1(request: ChainRequest):
    """Execute a chain of blocks (v1 API)."""
    return await chain_execute(request)


@app.post("/v1/chat")
async def chat_v1(request: ChatRequest):
    """Simple chat endpoint (v1 API)."""
    return await chat(request)


@app.post("/v1/chat/stream")
async def chat_stream_v1(request: ChatRequest):
    """Streaming chat endpoint (v1 API)."""
    return await chat_stream(request)


@app.post("/v1/upload")
async def upload_v1(file: UploadFile = File(...)):
    """File upload endpoint (v1 API).
    
    Accepts any file and stores it. Returns URL for processing.
    """
    import uuid
    import os
    import shutil
    
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())[:8]
        original_name = file.filename or "unknown"
        filename = f"{file_id}_{original_name}"
        filepath = os.path.join(DATA_DIR, filename)
        
        # Save uploaded file
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(filepath)
        
        # Return URL for processing
        base_url = os.getenv("API_BASE_URL", "https://ssdppg.onrender.com")
        return {
            "url": f"{base_url}/static/{filename}",
            "filename": original_name,
            "stored_as": filename,
            "size": file_size
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- ERROR HANDLERS --------------------

@app.exception_handler(404)
async def not_found(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "path": str(request.url)}
    )


@app.exception_handler(500)
async def server_error(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Server error", "detail": str(exc)}
    )


# Import asyncio for sleep
import asyncio


# -------------------- MONITORING & MEMORY BLOCKS --------------------

# Import Memory and Monitoring blocks
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from blocks.memory.src.block import MemoryBlock
    from blocks.monitoring.src.block import MonitoringBlock
    
    # Initialize blocks
    _memory_block = None
    _monitoring_block = None
    
    def get_memory_block():
        global _memory_block
        if _memory_block is None:
            _memory_block = MemoryBlock(None, {"max_size": 10000, "default_ttl": 3600})
            asyncio.create_task(_memory_block.initialize())
        return _memory_block
    
    def get_monitoring_block():
        global _monitoring_block
        if _monitoring_block is None:
            _monitoring_block = MonitoringBlock(None, {})
            _monitoring_block.memory_block = get_memory_block()
            asyncio.create_task(_monitoring_block.initialize())
        return _monitoring_block
    
    MEMORY_AVAILABLE = True
    MONITORING_AVAILABLE = True
    print("✅ Memory & Monitoring blocks loaded")
except Exception as e:
    MEMORY_AVAILABLE = False
    MONITORING_AVAILABLE = False
    print(f"⚠️ Memory/Monitoring blocks not available: {e}")


@app.get("/v1/leaderboard")
async def get_leaderboard():
    """Provider reliability leaderboard"""
    if not MONITORING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monitoring not available")
    block = get_monitoring_block()
    return await block.execute({"action": "leaderboard"})


@app.get("/v1/recommend")
async def recommend_provider():
    """AI-powered provider recommendation"""
    if not MONITORING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monitoring not available")
    block = get_monitoring_block()
    return await block.execute({"action": "recommend"})


@app.get("/v1/predict")
async def predictive_failover():
    """Predict potential failures before they happen"""
    if not MONITORING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monitoring not available")
    block = get_monitoring_block()
    return await block.execute({"action": "predictive_failover"})


@app.post("/v1/metrics/record")
async def record_metrics(request: dict):
    """Record call metrics for tracking"""
    if not MONITORING_AVAILABLE:
        return {"status": "no_op"}
    block = get_monitoring_block()
    return await block.execute({"action": "record_call", **request})


@app.get("/v1/system/health")
async def full_health():
    """Complete system health with predictions"""
    if not MONITORING_AVAILABLE:
        return await health_v1()
    
    block = get_monitoring_block()
    return await block.execute({"action": "health_report"})


# Memory block endpoints
@app.get("/v1/memory/stats")
async def memory_stats():
    """Get memory cache statistics"""
    if not MEMORY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Memory block not available")
    block = get_memory_block()
    return await block.execute({"action": "stats"})


@app.post("/v1/memory/{action}")
async def memory_operation(action: str, request: dict):
    """Memory cache operations: get, set, delete, flush, keys"""
    if not MEMORY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Memory block not available")
    
    if action not in ["get", "set", "delete", "flush", "keys", "exists"]:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
    
    block = get_memory_block()
    return await block.execute({"action": action, **request})


# -------------------- AUTH BLOCK --------------------

try:
    from blocks.auth.src.block import AuthBlock
    
    _auth_block = None
    
    def get_auth_block():
        global _auth_block
        if _auth_block is None:
            _auth_block = AuthBlock(None, {
                "rate_limit_default": 100,
                "rate_limit_window": 60,
                "master_key": os.getenv("CEREBRUM_MASTER_KEY")
            })
            _auth_block.memory_block = get_memory_block()
            asyncio.create_task(_auth_block.initialize())
        return _auth_block
    
    AUTH_AVAILABLE = True
    print("✅ Auth block loaded")
except Exception as e:
    AUTH_AVAILABLE = False
    print(f"⚠️ Auth block not available: {e}")


@app.post("/v1/auth/validate")
async def validate_key(request: dict):
    """Validate an API key"""
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Auth not available")
    block = get_auth_block()
    return await block.execute({"action": "validate", "key": request.get("key")})


@app.post("/v1/auth/keys")
async def create_key(request: dict):
    """Create a new API key (admin only)"""
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Auth not available")
    block = get_auth_block()
    return await block.execute({"action": "create_key", **request})


@app.get("/v1/auth/keys")
async def list_keys(admin_key: str):
    """List all API keys (admin only)"""
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Auth not available")
    block = get_auth_block()
    return await block.execute({"action": "list_keys", "admin_key": admin_key})


@app.post("/v1/auth/keys/revoke")
async def revoke_key(request: dict):
    """Revoke an API key"""
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Auth not available")
    block = get_auth_block()
    return await block.execute({"action": "revoke_key", **request})


@app.post("/v1/auth/keys/rotate")
async def rotate_key(request: dict):
    """Rotate an API key"""
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Auth not available")
    block = get_auth_block()
    return await block.execute({"action": "rotate_key", **request})


@app.post("/v1/auth/check")
async def check_permission(request: dict):
    """Check if key has a permission"""
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Auth not available")
    block = get_auth_block()
    return await block.execute({"action": "check_permission", **request})


@app.get("/v1/auth/usage")
async def get_usage(key: str, admin_key: Optional[str] = None):
    """Get usage stats for a key"""
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Auth not available")
    block = get_auth_block()
    return await block.execute({"action": "get_usage", "key": key, "admin_key": admin_key})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
# CORS fix deployed - Sat Apr 11 22:21:38 UTC 2026
# Redeploy trigger: Sat Apr 11 22:53:40 UTC 2026
