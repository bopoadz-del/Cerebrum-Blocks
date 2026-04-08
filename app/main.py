"""Main FastAPI application for the AI Block System - Render Ready."""

import os
import sys

# Add app to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import aiofiles
import hashlib
import time
import json

# Import core components
from app.core import CerebrumClient, chain, StandardResponse
from app.blocks import BLOCK_REGISTRY, get_all_blocks

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="AI Block System",
    description="Build AI Like Lego - 13 Blocks. Infinite Possibilities.",
    version="1.0.0",
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

# --------------------- CORE ENDPOINTS ---------------------

@app.get("/")
async def root():
    """Root endpoint with system info."""
    return {
        "status": "AI Block System running",
        "version": "1.0.0",
        "blocks_available": len(BLOCK_REGISTRY),
        "environment": "render" if os.getenv("RENDER") else "development",
        "documentation": "/docs",
        "endpoints": {
            "blocks": "/blocks",
            "execute": "/execute",
            "chain": "/chain",
            "ingest": "/ingest",
            "health": "/health"
        }
    }

@app.get("/blocks")
async def list_blocks():
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

# --------------------- INGEST ENDPOINT ---------------------

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

# --------------------- EXECUTE ENDPOINT ---------------------

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

# --------------------- CHAIN ENDPOINT ---------------------

@app.post("/chain")
async def execute_chain(request: ChainRequest):
    """Execute a chain of blocks."""
    try:
        # Use internal client pointing to self
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

# --------------------- DRIVE-SPECIFIC ENDPOINTS ---------------------

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

# --------------------- HEALTH & STATS ---------------------

@app.get("/health")
async def health():
    """Health check endpoint for Render."""
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
    print("🚀 AI Block System v1.0.0")
    print("=" * 60)
    print(f"📁 Data Directory: {DATA_DIR}")
    print(f"🌐 Server: http://{HOST}:{PORT}")
    print(f"📚 API Docs: http://{HOST}:{PORT}/docs")
    print(f"📊 Health: http://{HOST}:{PORT}/health")
    print("-" * 60)
    print(f"📦 Available Blocks ({len(BLOCK_REGISTRY)}):")
    for i, name in enumerate(BLOCK_REGISTRY.keys(), 1):
        print(f"   {i}. {name}")
    print("=" * 60)

# --------------------- MAIN ---------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
