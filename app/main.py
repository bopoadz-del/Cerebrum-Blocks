"""Cerebrum Blocks - Simple Block Execution API."""

import os
import sys
import time
import json
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Import blocks
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.blocks import BLOCK_REGISTRY, get_all_blocks

app = FastAPI(
    title="Cerebrum Blocks",
    description="Build AI Like Lego - Simple Block Execution API",
    version="2.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store block instances
block_instances: Dict[str, Any] = {}
DATA_DIR = os.getenv("DATA_DIR", "./data")
os.makedirs(DATA_DIR, exist_ok=True)


# -------------------- MODELS --------------------

class ExecuteRequest(BaseModel):
    block: str = Field(..., description="Block name (chat, pdf, ocr, voice, etc.)")
    input: Any = Field(..., description="Input data for the block")
    params: Optional[Dict[str, Any]] = Field(default={}, description="Block parameters")


class ChainRequest(BaseModel):
    steps: List[Dict[str, Any]] = Field(..., description="Chain of blocks to execute")
    initial_input: Any = Field(..., description="Starting input")


class ChatRequest(BaseModel):
    message: str
    model: str = "gpt-3.5-turbo"
    stream: bool = False


# -------------------- BLOCKS --------------------

@app.get("/")
def root():
    """API info."""
    return {
        "name": "Cerebrum Blocks",
        "version": "2.0.0",
        "tagline": "Build AI Like Lego",
        "blocks": len(BLOCK_REGISTRY),
        "endpoints": {
            "blocks": "/blocks",
            "execute": "/execute",
            "chain": "/chain",
            "chat": "/chat",
            "health": "/health",
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
        try:
            if name not in block_instances:
                block_instances[name] = block_class()
            instance = block_instances[name]
            
            blocks.append({
                "name": name,
                "version": instance.config.version,
                "description": instance.config.description,
                "inputs": instance.config.supported_inputs,
                "outputs": instance.config.supported_outputs,
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
def get_block(block_name: str):
    """Get block details."""
    if block_name not in BLOCK_REGISTRY:
        raise HTTPException(404, f"Block '{block_name}' not found")
    
    if block_name not in block_instances:
        block_instances[block_name] = BLOCK_REGISTRY[block_name]()
    
    instance = block_instances[block_name]
    return {
        "name": block_name,
        "config": {
            "version": instance.config.version,
            "description": instance.config.description,
            "inputs": instance.config.supported_inputs,
            "outputs": instance.config.supported_outputs,
        },
        "stats": instance.get_stats()
    }


# -------------------- EXECUTE --------------------

@app.post("/execute")
async def execute(request: ExecuteRequest):
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
        
        try:
            if block_name not in block_instances:
                block_instances[block_name] = BLOCK_REGISTRY[block_name]()
            
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
    return get_block(block_name)


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
