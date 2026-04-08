"""Main FastAPI application for Cerebrum Blocks - SaaS Ready."""

import os
import sys

# Add app to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, AsyncGenerator
import aiofiles
import hashlib
import time
import json
import asyncio

# Import core components
from app.core import CerebrumClient, chain, StandardResponse
from app.blocks import BLOCK_REGISTRY, get_all_blocks
from app.core.api_keys import (
    get_key_manager, require_api_key, optional_api_key, 
    APIKeyManager, Tier
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Cerebrum Blocks",
    description="Build AI Like Lego - 16 Blocks. One API Key. Infinite Possibilities.",
    version="2.0.0",
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

# Ensure data directory exists (with fallback for local dev)
try:
    os.makedirs(DATA_DIR, exist_ok=True)
except PermissionError:
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    os.makedirs(DATA_DIR, exist_ok=True)

# Store block instances
block_instances = {}
key_manager = get_key_manager()

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
    provider: str = Field(default="openai", description="Provider: openai, anthropic, groq")
    stream: bool = Field(default=False, description="Stream the response")

class ChatCompletionRequest(BaseModel):
    model: str = Field(default="gpt-3.5-turbo", description="Model to use")
    messages: List[Dict[str, Any]] = Field(..., description="List of messages")
    max_tokens: int = Field(default=1000, description="Maximum tokens")
    temperature: float = Field(default=0.7, ge=0, le=2, description="Sampling temperature")
    stream: bool = Field(default=False, description="Stream the response")

class VectorAddRequest(BaseModel):
    documents: List[Dict[str, Any]] = Field(..., description="Documents to add")
    collection: str = Field(default="default", description="Collection name")

class VectorSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    collection: str = Field(default="default", description="Collection name")
    top_k: int = Field(default=5, description="Number of results")

class AgentExecuteRequest(BaseModel):
    agent_id: str = Field(..., description="Agent ID to execute")
    input: Dict[str, Any] = Field(default_factory=dict, description="Input parameters")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Context data")

class CreateKeyRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    tier: str = Field(default="free", description="Tier: free, pro, enterprise")

class UpgradeTierRequest(BaseModel):
    key_id: str
    new_tier: str
    payment_method_id: Optional[str] = None

# --------------------- HEALTH & STATUS ---------------------

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
            "version": "2.0.0",
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

# --------------------- CHAT ENDPOINTS ---------------------

@app.post("/v1/chat")
async def v1_chat(
    request: ChatRequest, 
    key_data: Dict[str, Any] = Depends(require_api_key)
):
    """Chat completions endpoint with streaming support."""
    if "chat" not in BLOCK_REGISTRY:
        raise HTTPException(500, "Chat block not available")
    
    start_time = time.time()
    
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
        
        response_time = int((time.time() - start_time) * 1000)
        tokens_used = result.get("result", {}).get("tokens_total", 0)
        
        # Log usage
        await key_manager.log_usage(
            key_id=key_data["id"],
            endpoint="/v1/chat",
            block_name="chat",
            tokens=tokens_used,
            response_time_ms=response_time,
            status_code=200
        )
        
        return {
            "text": result.get("result", {}).get("text", ""),
            "model": request.model,
            "provider": request.provider,
            "tokens_total": tokens_used,
            "finish_reason": result.get("result", {}).get("finish_reason", ""),
        }
    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        await key_manager.log_usage(
            key_id=key_data["id"],
            endpoint="/v1/chat",
            block_name="chat",
            response_time_ms=response_time,
            status_code=500
        )
        raise HTTPException(500, f"Chat failed: {str(e)}")


@app.post("/v1/chat/stream")
async def v1_chat_stream(
    request: ChatRequest, 
    key_data: Dict[str, Any] = Depends(require_api_key)
):
    """Streaming chat completions endpoint with SSE."""
    if "chat" not in BLOCK_REGISTRY:
        raise HTTPException(500, "Chat block not available")
    
    async def event_stream() -> AsyncGenerator[str, None]:
        start_time = time.time()
        total_tokens = 0
        
        try:
            if "chat" not in block_instances:
                block_instances["chat"] = BLOCK_REGISTRY["chat"]()
            
            block = block_instances["chat"]
            
            # Check if block has native streaming
            if hasattr(block, 'stream'):
                async for chunk in block.stream(request.message, {
                    "model": request.model,
                    "system": request.system,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "provider": request.provider,
                }):
                    content = chunk.get("content", "")
                    total_tokens += chunk.get("tokens", 0)
                    data = json.dumps({"content": content, "done": False})
                    yield f"data: {data}\n\n"
            else:
                # Fallback to regular execute and stream word by word
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
                else:
                    text = result.get("result", {}).get("text", "")
                    words = text.split()
                    for word in words:
                        data = json.dumps({"content": word + " ", "done": False})
                        yield f"data: {data}\n\n"
                        await asyncio.sleep(0.05)  # Simulate typing
            
            # Final message
            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
            yield "data: [DONE]\n\n"
            
            # Log usage
            response_time = int((time.time() - start_time) * 1000)
            await key_manager.log_usage(
                key_id=key_data["id"],
                endpoint="/v1/chat/stream",
                block_name="chat",
                tokens=total_tokens or len(words),
                response_time_ms=response_time,
                status_code=200
            )
            
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            await key_manager.log_usage(
                key_id=key_data["id"],
                endpoint="/v1/chat/stream",
                block_name="chat",
                response_time_ms=response_time,
                status_code=500
            )
            yield f"data: {json.dumps({'content': f'[Error: {str(e)}]', 'done': True})}\n\n"
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


@app.post("/api/v1/chat/completions")
async def api_v1_chat_completions(
    request: ChatCompletionRequest, 
    key_data: Dict[str, Any] = Depends(require_api_key)
):
    """OpenAI-compatible chat completions endpoint."""
    if "chat" not in BLOCK_REGISTRY:
        raise HTTPException(500, "Chat block not available")
    
    start_time = time.time()
    
    try:
        if "chat" not in block_instances:
            block_instances["chat"] = BLOCK_REGISTRY["chat"]()
        
        block = block_instances["chat"]
        
        # Extract the last user message
        last_message = ""
        system_message = "You are a helpful assistant."
        for msg in request.messages:
            if msg.get("role") == "user":
                last_message = msg.get("content", "")
            elif msg.get("role") == "system":
                system_message = msg.get("content", system_message)
        
        result = await block.execute(last_message, {
            "model": request.model,
            "system": system_message,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "provider": "openai" if "gpt" in request.model else "groq",
            "stream": False,
        })
        
        response_time = int((time.time() - start_time) * 1000)
        tokens_used = result.get("result", {}).get("tokens_total", 0)
        
        # Log usage
        await key_manager.log_usage(
            key_id=key_data["id"],
            endpoint="/api/v1/chat/completions",
            block_name="chat",
            tokens=tokens_used,
            response_time_ms=response_time,
            status_code=200
        )
        
        # Return OpenAI-compatible format
        return {
            "id": f"chatcmpl-{hashlib.md5(str(time.time()).encode()).hexdigest()[:16]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result.get("result", {}).get("text", "")
                },
                "finish_reason": result.get("result", {}).get("finish_reason", "stop")
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": tokens_used,
                "total_tokens": tokens_used
            }
        }
    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        await key_manager.log_usage(
            key_id=key_data["id"],
            endpoint="/api/v1/chat/completions",
            block_name="chat",
            response_time_ms=response_time,
            status_code=500
        )
        raise HTTPException(500, f"Chat completion failed: {str(e)}")


# --------------------- BLOCKS ENDPOINTS ---------------------

@app.get("/v1/blocks")
async def v1_list_blocks(key_data: Dict[str, Any] = Depends(require_api_key)):
    """List all available blocks with tier-based filtering."""
    tier = key_data["tier"]
    tier_limits = {
        Tier.FREE: ["chat", "pdf", "ocr", "voice", "translate"],
        Tier.PRO: "all",
        Tier.ENTERPRISE: "all",
    }
    
    allowed_blocks = tier_limits.get(tier, [])
    
    blocks = []
    for name, block_class in get_all_blocks().items():
        # Filter by tier
        if allowed_blocks != "all" and name not in allowed_blocks:
            continue
            
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
        "tier": tier.value,
        "categories": {
            "ai": ["pdf", "ocr", "chat", "voice", "search", "image", "translate", "code", "web"],
            "drive": ["google_drive", "onedrive", "local_drive", "android_drive"]
        }
    }


@app.post("/v1/execute")
async def v1_execute(
    request: ProcessRequest,
    key_data: Dict[str, Any] = Depends(require_api_key)
):
    """Execute a single block with usage tracking."""
    block_name = request.block
    
    # Check tier permissions
    tier = key_data["tier"]
    tier_limits = {
        Tier.FREE: ["chat", "pdf", "ocr", "voice", "translate"],
        Tier.PRO: "all",
        Tier.ENTERPRISE: "all",
    }
    allowed = tier_limits.get(tier, [])
    
    if allowed != "all" and block_name not in allowed:
        raise HTTPException(403, f"Block '{block_name}' not available on your tier. Upgrade to Pro.")
    
    if block_name not in BLOCK_REGISTRY:
        raise HTTPException(404, f"Block '{block_name}' not found")
    
    start_time = time.time()
    
    try:
        if block_name not in block_instances:
            block_instances[block_name] = BLOCK_REGISTRY[block_name]()
        
        block = block_instances[block_name]
        result = await block.execute(request.input, request.params or {})
        
        response_time = int((time.time() - start_time) * 1000)
        
        # Log usage
        await key_manager.log_usage(
            key_id=key_data["id"],
            endpoint="/v1/execute",
            block_name=block_name,
            response_time_ms=response_time,
            status_code=200
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        await key_manager.log_usage(
            key_id=key_data["id"],
            endpoint="/v1/execute",
            block_name=block_name,
            response_time_ms=response_time,
            status_code=500
        )
        raise HTTPException(500, f"Execution failed: {str(e)}")


@app.post("/v1/chain")
async def v1_execute_chain(
    request: ChainRequest,
    key_data: Dict[str, Any] = Depends(require_api_key)
):
    """Execute a chain of blocks with usage tracking."""
    start_time = time.time()
    
    try:
        base_url = f"http://{HOST}:{PORT}"
        client = CerebrumClient(base_url=base_url)
        chain_builder = chain(client)
        
        for step in request.steps:
            chain_builder.then(step["block"], step.get("params", {}))
        
        result = await chain_builder.run(request.initial_input)
        
        response_time = int((time.time() - start_time) * 1000)
        
        # Log usage
        await key_manager.log_usage(
            key_id=key_data["id"],
            endpoint="/v1/chain",
            response_time_ms=response_time,
            status_code=200
        )
        
        return {
            "status": "success" if result.success else "partial_failure",
            "steps_executed": len(result.steps),
            "total_time_ms": result.total_time_ms,
            "final_output": result.final_output,
            "step_results": result.steps
        }
    except Exception as e:
        response_time = int((time.time() - start_time) * 1000)
        await key_manager.log_usage(
            key_id=key_data["id"],
            endpoint="/v1/chain",
            response_time_ms=response_time,
            status_code=500
        )
        raise HTTPException(500, f"Chain execution failed: {str(e)}")


# --------------------- VECTOR SEARCH ENDPOINTS ---------------------

@app.post("/v1/vector/add")
async def v1_vector_add(
    request: VectorAddRequest, 
    key_data: Dict[str, Any] = Depends(require_api_key)
):
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
        
        await key_manager.log_usage(
            key_id=key_data["id"],
            endpoint="/v1/vector/add",
            block_name="vector_search",
            status_code=200
        )
        
        return {
            "status": "success",
            "collection": request.collection,
            "documents_added": len(request.documents),
        }
    except Exception as e:
        raise HTTPException(500, f"Vector add failed: {str(e)}")


@app.post("/v1/vector/search")
async def v1_vector_search(
    request: VectorSearchRequest, 
    key_data: Dict[str, Any] = Depends(require_api_key)
):
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
        
        await key_manager.log_usage(
            key_id=key_data["id"],
            endpoint="/v1/vector/search",
            block_name="vector_search",
            status_code=200
        )
        
        return {
            "results": result.get("result", {}).get("results", []),
            "query": request.query,
            "collection": request.collection,
        }
    except Exception as e:
        raise HTTPException(500, f"Vector search failed: {str(e)}")


# --------------------- DOCUMENT UPLOAD ENDPOINTS ---------------------

@app.post("/api/v1/documents/upload/public")
async def api_v1_documents_upload_public(
    file: UploadFile = File(...),
    key_data: Dict[str, Any] = Depends(require_api_key)
):
    """Upload a document for public access."""
    try:
        content = await file.read()
        file_id = hashlib.sha256(content).hexdigest()
        file_path = os.path.join(DATA_DIR, file_id)
        
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        await key_manager.log_usage(
            key_id=key_data["id"],
            endpoint="/api/v1/documents/upload/public",
            request_size=len(content),
            status_code=200
        )
        
        return {
            "status": "success",
            "file_key": file_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "url": f"/files/{file_id}"
        }
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")


@app.post("/api/v1/documents/upload/chat")
async def api_v1_documents_upload_chat(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    key_data: Dict[str, Any] = Depends(require_api_key)
):
    """Upload a document for chat context."""
    try:
        content = await file.read()
        file_id = hashlib.sha256(content).hexdigest()
        file_path = os.path.join(DATA_DIR, f"chat_{file_id}")
        
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        await key_manager.log_usage(
            key_id=key_data["id"],
            endpoint="/api/v1/documents/upload/chat",
            request_size=len(content),
            status_code=200
        )
        
        return {
            "status": "success",
            "file_key": file_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "conversation_id": conversation_id
        }
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")


@app.get("/files/{file_id}")
async def get_file(file_id: str):
    """Serve an uploaded file."""
    file_path = os.path.join(DATA_DIR, file_id)
    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found")
    return FileResponse(file_path)


# --------------------- AGENT ENDPOINTS ---------------------

@app.get("/api/v1/agent/v2/status/enhanced")
async def api_v1_agent_v2_status_enhanced(
    key_data: Dict[str, Any] = Depends(require_api_key)
):
    """Get enhanced agent status."""
    return {
        "status": "ready",
        "version": "2.0",
        "capabilities": ["chat", "file_upload", "streaming"],
        "agents": [
            {"id": "default", "name": "Default Agent", "status": "active"}
        ]
    }


@app.post("/api/v1/agent/v2/execute")
async def api_v1_agent_v2_execute(
    request: AgentExecuteRequest,
    key_data: Dict[str, Any] = Depends(require_api_key)
):
    """Execute an agent with the given input."""
    try:
        if "chat" not in block_instances:
            block_instances["chat"] = BLOCK_REGISTRY["chat"]()
        
        block = block_instances["chat"]
        
        input_text = request.input.get("message", "") if request.input else ""
        
        result = await block.execute(input_text, {
            "model": "gpt-3.5-turbo",
            "system": "You are a helpful assistant.",
            "max_tokens": 1000,
            "temperature": 0.7,
            "provider": "openai",
            "stream": False,
        })
        
        await key_manager.log_usage(
            key_id=key_data["id"],
            endpoint="/api/v1/agent/v2/execute",
            block_name="chat",
            tokens=result.get("result", {}).get("tokens_total", 0),
            status_code=200
        )
        
        return {
            "status": "success",
            "agent_id": request.agent_id,
            "result": {
                "text": result.get("result", {}).get("text", ""),
                "tokens_used": result.get("result", {}).get("tokens_total", 0)
            }
        }
    except Exception as e:
        raise HTTPException(500, f"Agent execution failed: {str(e)}")


# --------------------- API KEY MANAGEMENT ENDPOINTS ---------------------

@app.post("/v1/keys/create")
async def create_api_key(request: CreateKeyRequest):
    """Create a new API key."""
    try:
        tier = Tier(request.tier.lower())
    except ValueError:
        tier = Tier.FREE
    
    result = key_manager.generate_key(
        name=request.name,
        email=request.email,
        tier=tier
    )
    
    # Create Stripe customer if email provided
    if request.email and request.email.strip():
        await key_manager.create_stripe_customer(result["key_id"], request.email)
    
    return result


@app.get("/v1/keys/{key_id}/usage")
async def get_key_usage(
    key_id: str,
    days: int = 30,
    key_data: Dict[str, Any] = Depends(require_api_key)
):
    """Get usage statistics for an API key."""
    # Only allow users to see their own usage unless admin
    if key_data["id"] != key_id:
        raise HTTPException(403, "Can only view your own usage")
    
    stats = key_manager.get_usage_stats(key_id, days)
    limits = {
        Tier.FREE: {"requests": 1000, "tokens": 100000},
        Tier.PRO: {"requests": 50000, "tokens": 5000000},
        Tier.ENTERPRISE: {"requests": -1, "tokens": -1},
    }
    
    tier_limits = limits.get(key_data["tier"], limits[Tier.FREE])
    
    return {
        "key_id": key_id,
        "tier": key_data["tier"].value,
        **stats,
        "limits": tier_limits,
    }


@app.post("/v1/keys/{key_id}/upgrade")
async def upgrade_key_tier(
    key_id: str,
    request: UpgradeTierRequest,
    key_data: Dict[str, Any] = Depends(require_api_key)
):
    """Upgrade an API key to a new tier."""
    if key_data["id"] != key_id:
        raise HTTPException(403, "Can only upgrade your own key")
    
    try:
        new_tier = Tier(request.new_tier.lower())
    except ValueError:
        raise HTTPException(400, "Invalid tier")
    
    # TODO: Process payment with Stripe if upgrading to paid tier
    
    success = await key_manager.upgrade_tier(key_id, new_tier)
    
    if not success:
        raise HTTPException(500, "Failed to upgrade tier")
    
    return {"status": "success", "new_tier": new_tier.value}


@app.delete("/v1/keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    key_data: Dict[str, Any] = Depends(require_api_key)
):
    """Revoke an API key."""
    if key_data["id"] != key_id:
        raise HTTPException(403, "Can only revoke your own key")
    
    success = key_manager.revoke_key(key_id)
    
    if not success:
        raise HTTPException(500, "Failed to revoke key")
    
    return {"status": "success", "message": "API key revoked"}


# --------------------- STATIC FILES ---------------------

# Serve landing page at root
@app.get("/", response_class=FileResponse)
async def root():
    """Serve the landing page."""
    landing_file = os.path.join(os.path.dirname(__file__), "static", "landing", "index.html")
    if os.path.exists(landing_file):
        return FileResponse(landing_file)
    # Fallback to blocks explorer
    static_file = os.path.join(os.path.dirname(__file__), "static", "blocks.html")
    return FileResponse(static_file)


# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


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
    print("🚀 Cerebrum Blocks v2.0.0 - SaaS Ready")
    print("=" * 60)
    print(f"📁 Data Directory: {DATA_DIR}")
    print(f"🌐 Server: http://{HOST}:{PORT}")
    print(f"📚 API Docs: http://{HOST}:{PORT}/docs")
    print(f"🔐 API Key System: {'Enabled' if key_manager else 'Disabled'}")
    print("-" * 60)
    print(f"📦 Available Blocks ({len(BLOCK_REGISTRY)}):")
    for i, name in enumerate(BLOCK_REGISTRY.keys(), 1):
        print(f"   {i}. {name}")
    print("=" * 60)


# --------------------- MAIN ---------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
