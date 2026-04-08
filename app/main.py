"""Main FastAPI application for Cerebrum Blocks - Render Ready."""

import os
import sys

# Add app to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import aiofiles
import hashlib
import time
import json
import asyncio

# Import core components
from app.core import CerebrumClient, chain, StandardResponse
from app.blocks import BLOCK_REGISTRY, get_all_blocks
from app.core.auth import auth, require_api_key

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Cerebrum Blocks",
    description="Build AI Like Lego - 13 Blocks. One API Key. Infinite Possibilities.",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS configuration - allow all for Render deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Store block instances
block_instances = {}

# --------------------- REQUEST MODELS ---------------------

class IngestRequest(BaseModel):
    metadata: Optional[Dict[str, Any]] = None

class ProcessRequest(BaseModel):
    block: str
    input: Any
    params: Optional[Dict[str, Any]] = None

class ChainRequest(BaseModel):
    steps: List[Dict[str, Any]]
    initial_input: Any

class ChatRequest(BaseModel):
    message: str = Field(..., description="The message to send")
    model: str = Field(default="gpt-3.5-turbo", description="Model to use")
    system: str = Field(default="You are a helpful assistant.", description="System prompt")
    max_tokens: int = Field(default=1000, description="Maximum tokens")
    temperature: float = Field(default=0.7, ge=0, le=2, description="Sampling temperature")
    provider: str = Field(default="openai", description="Provider: openai, anthropic, mock")
    stream: bool = Field(default=False, description="Stream the response")

class VectorAddRequest(BaseModel):
    documents: List[Dict[str, Any]] = Field(..., description="Documents to add")
    collection: str = Field(default="default", description="Collection name")

class VectorSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    collection: str = Field(default="default", description="Collection name")
    top_k: int = Field(default=5, description="Number of results")

# --------------------- V1 API ENDPOINTS ---------------------

@app.get("/v1/health")
async def v1_health():
    """Health check endpoint."""
    try:
        disk_usage = None
        try:
            import shutil
            total, used, free = shutil.disk_usage(DATA_DIR)
            disk_usage = {
                "total_gb": round(total / (2**30), 2),
                "used_gb": round(used / (2**30), 2),
                "free_gb": round(free / (2**30), 2)
            }
        except:
            pass
        
        return {
            "status": "healthy",
            "version": "1.1.0",
            "blocks_loaded": len(block_instances),
            "blocks_available": len(BLOCK_REGISTRY),
            "data_dir": DATA_DIR,
            "disk_usage": disk_usage,
            "timestamp": time.time()
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/v1/blocks")
async def v1_list_blocks(_: Dict[str, Any] = Depends(require_api_key)):
    """List all available blocks."""
    blocks = []
    for name, block_class in get_all_blocks().items():
        try:
            if name not in block_instances:
                block_instances[name] = block_class()
            instance = block_instances[name]
            
            blocks.append({
                "name": name,
                "version": instance.config.version,
                "description": instance.config.description,
                "requires_api_key": instance.config.requires_api_key,
                "supported_inputs": instance.config.supported_inputs,
                "supported_outputs": instance.config.supported_outputs
            })
        except Exception as e:
            blocks.append({
                "name": name,
                "error": str(e),
                "status": "failed_to_load"
            })
    
    return {
        "blocks": blocks,
        "total": len(blocks),
        "categories": {
            "ai": ["pdf", "ocr", "chat", "voice", "search", "image", "translate", "code", "web"],
            "drive": ["google_drive", "onedrive", "local_drive", "android_drive"]
        }
    }

@app.post("/v1/chat")
async def v1_chat(request: ChatRequest, _: Dict[str, Any] = Depends(require_api_key)):
    """Chat completions endpoint."""
    if "chat" not in BLOCK_REGISTRY:
        raise HTTPException(500, "Chat block not available")
    
    try:
        if "chat" not in block_instances:
            block_instances["chat"] = BLOCK_REGISTRY["chat"]()
        
        block = block_instances["chat"]
        
        result = await block.execute(request.message, {
            "model": request.model,
            "system": request.system,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "provider": request.provider,
            "stream": False,
        })
        
        # Flatten the response for the SDK
        response_data = {
            "text": result.get("result", {}).get("text", ""),
            "model": request.model,
            "provider": request.provider,
            "tokens_total": result.get("result", {}).get("tokens_total", 0),
            "finish_reason": result.get("result", {}).get("finish_reason", ""),
        }
        
        return response_data
    except Exception as e:
        raise HTTPException(500, f"Chat failed: {str(e)}")

@app.post("/v1/chat/stream")
async def v1_chat_stream(request: ChatRequest, _: Dict[str, Any] = Depends(require_api_key)):
    """Streaming chat completions endpoint."""
    if "chat" not in BLOCK_REGISTRY:
        raise HTTPException(500, "Chat block not available")
    
    async def event_stream():
        try:
            if "chat" not in block_instances:
                block_instances["chat"] = BLOCK_REGISTRY["chat"]()
            
            block = block_instances["chat"]
            
            result = await block.execute(request.message, {
                "model": request.model,
                "system": request.system,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "provider": request.provider,
                "stream": True,
            })
            
            stream_gen = result.get("result", {}).get("stream")
            if stream_gen:
                async for chunk in stream_gen:
                    data = json.dumps(chunk)
                    yield f"data: {data}\n\n"
                yield "data: [DONE]\n\n"
            else:
                text = result.get("result", {}).get("text", "")
                yield f"data: {json.dumps({'text': text, 'done': True})}\n\n"
                yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'text': f'[Error: {str(e)}]', 'done': True})}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

@app.post("/v1/vector/add")
async def v1_vector_add(request: VectorAddRequest, _: Dict[str, Any] = Depends(require_api_key)):
    """Add documents to vector search."""
    if "vector_search" not in BLOCK_REGISTRY:
        raise HTTPException(500, "Vector search block not available")
    
    try:
        if "vector_search" not in block_instances:
            block_instances["vector_search"] = BLOCK_REGISTRY["vector_search"]()
        
        block = block_instances["vector_search"]
        result = await block.execute(request.documents, {
            "operation": "add",
            "collection": request.collection,
        })
        
        return {
            "status": "success",
            "collection": request.collection,
            "documents_added": len(request.documents),
        }
    except Exception as e:
        raise HTTPException(500, f"Vector add failed: {str(e)}")

@app.post("/v1/vector/search")
async def v1_vector_search(request: VectorSearchRequest, _: Dict[str, Any] = Depends(require_api_key)):
    """Search vector database."""
    if "vector_search" not in BLOCK_REGISTRY:
        raise HTTPException(500, "Vector search block not available")
    
    try:
        if "vector_search" not in block_instances:
            block_instances["vector_search"] = BLOCK_REGISTRY["vector_search"]()
        
        block = block_instances["vector_search"]
        result = await block.execute(request.query, {
            "operation": "search",
            "collection": request.collection,
            "top_k": request.top_k,
        })
        
        return {
            "results": result.get("result", {}).get("results", []),
            "query": request.query,
            "collection": request.collection,
        }
    except Exception as e:
        raise HTTPException(500, f"Vector search failed: {str(e)}")

# --------------------- LEGACY ENDPOINTS (Backward Compatible) ---------------------

@app.get("/")
async def root():
    """Root endpoint with system info."""
    return {
        "status": "Cerebrum Blocks running",
        "version": "1.1.0",
        "blocks_available": len(BLOCK_REGISTRY),
        "environment": "render" if os.getenv("RENDER") else "development",
        "documentation": "/docs",
        "endpoints": {
            "v1_api": "/v1",
            "blocks": "/blocks",
            "execute": "/execute",
            "chain": "/chain",
            "health": "/health"
        }
    }

@app.get("/blocks")
async def list_blocks():
    """List all available blocks (legacy)."""
    return await v1_list_blocks({"user": "legacy", "tier": "unlimited", "valid": True})

@app.get("/blocks/{block_name}")
async def get_block_info(block_name: str):
    """Get detailed info about a specific block."""
    if block_name not in BLOCK_REGISTRY:
        raise HTTPException(404, f"Block '{block_name}' not found")
    
    try:
        if block_name not in block_instances:
            block_instances[block_name] = BLOCK_REGISTRY[block_name]()
        
        instance = block_instances[block_name]
        
        return {
            "name": block_name,
            "config": {
                "version": instance.config.version,
                "description": instance.config.description,
                "requires_api_key": instance.config.requires_api_key,
                "supported_inputs": instance.config.supported_inputs,
                "supported_outputs": instance.config.supported_outputs
            },
            "stats": instance.get_stats()
        }
    except Exception as e:
        raise HTTPException(500, f"Error loading block: {str(e)}")

@app.post("/ingest")
async def ingest(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    base64_data: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None)
):
    """Ingest a file into the system."""
    start = time.time()
    request_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:12]
    
    file_id = None
    file_path = None
    
    try:
        if file:
            content = await file.read()
            file_id = hashlib.sha256(content).hexdigest()
            file_path = os.path.join(DATA_DIR, file_id)
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
        elif url:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    content = await response.read()
                    file_id = hashlib.sha256(content).hexdigest()
                    file_path = os.path.join(DATA_DIR, file_id)
                    async with aiofiles.open(file_path, "wb") as f:
                        await f.write(content)
        elif base64_data:
            import base64
            content = base64.b64decode(base64_data)
            file_id = hashlib.sha256(content).hexdigest()
            file_path = os.path.join(DATA_DIR, file_id)
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
        else:
            raise HTTPException(400, "Provide a file, url, or base64_data")
        
        meta = json.loads(metadata) if metadata else {}
        processing_time = int((time.time() - start) * 1000)
        
        return {
            "block": "ingest",
            "request_id": request_id,
            "status": "success",
            "result": {"stored": True, "file_path": file_path},
            "confidence": 1.0,
            "metadata": meta,
            "source_id": file_id,
            "processing_time_ms": processing_time
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Ingestion failed: {str(e)}")

@app.post("/execute")
async def execute(request: ProcessRequest):
    """Execute a single block."""
    block_name = request.block
    
    if block_name not in BLOCK_REGISTRY:
        raise HTTPException(404, f"Block '{block_name}' not found. Available: {list(BLOCK_REGISTRY.keys())}")
    
    try:
        if block_name not in block_instances:
            block_instances[block_name] = BLOCK_REGISTRY[block_name]()
        
        block = block_instances[block_name]
        result = await block.execute(request.input, request.params or {})
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Execution failed: {str(e)}")

@app.post("/chain")
async def execute_chain(request: ChainRequest):
    """Execute a chain of blocks."""
    try:
        base_url = f"http://{HOST}:{PORT}"
        client = CerebrumClient(base_url=base_url)
        chain_builder = chain(client)
        
        for step in request.steps:
            chain_builder.then(step["block"], step.get("params", {}))
        
        result = await chain_builder.run(request.initial_input)
        
        return {
            "status": "success" if result.success else "partial_failure",
            "steps_executed": len(result.steps),
            "total_time_ms": result.total_time_ms,
            "final_output": result.final_output,
            "step_results": result.steps
        }
    except Exception as e:
        raise HTTPException(500, f"Chain execution failed: {str(e)}")

@app.post("/drive/{drive_name}/{operation}")
async def drive_operation(drive_name: str, operation: str, params: Dict[str, Any] = None):
    """Direct drive operation endpoint."""
    params = params or {}
    params["operation"] = operation
    
    valid_drives = ["google_drive", "onedrive", "local_drive", "android_drive"]
    if drive_name not in valid_drives:
        raise HTTPException(404, f"Drive '{drive_name}' not found. Available: {valid_drives}")
    
    try:
        if drive_name not in block_instances:
            block_instances[drive_name] = BLOCK_REGISTRY[drive_name]()
        
        block = block_instances[drive_name]
        result = await block.process(params.get("input", {}), params)
        return result
    except Exception as e:
        raise HTTPException(500, f"Drive operation failed: {str(e)}")

@app.get("/health")
async def health():
    """Health check endpoint for Render."""
    return await v1_health()

@app.get("/stats")
async def stats():
    """Get statistics for all blocks."""
    all_stats = []
    for name, instance in block_instances.items():
        try:
            all_stats.append(instance.get_stats())
        except:
            pass
    
    return {
        "blocks": all_stats,
        "total_executions": sum(s.get("execution_count", 0) for s in all_stats),
        "data_directory": DATA_DIR,
        "disk_persisted": os.getenv("RENDER_DISK_NAME") is not None
    }

# --------------------- ERROR HANDLERS ---------------------

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "detail": str(exc.detail) if hasattr(exc, 'detail') else str(exc)}
    )

@app.exception_handler(500)
async def server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# --------------------- STARTUP ---------------------

@app.on_event("startup")
async def startup():
    """Initialize on startup."""
    print("=" * 60)
    print("🚀 Cerebrum Blocks v1.1.0")
    print("=" * 60)
    print(f"📁 Data Directory: {DATA_DIR}")
    print(f"🌐 Server: http://{HOST}:{PORT}")
    print(f"📚 API Docs: http://{HOST}:{PORT}/docs")
    print(f"🔐 API Key Auth: {'Enabled' if auth._keys else 'Development Mode (no keys required)'}")
    print("-" * 60)
    print(f"📦 Available Blocks ({len(BLOCK_REGISTRY)}):")
    for i, name in enumerate(BLOCK_REGISTRY.keys(), 1):
        print(f"   {i}. {name}")
    print("=" * 60)

# --------------------- MAIN ---------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
