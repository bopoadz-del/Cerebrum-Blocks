"""Cerebrum Blocks - Simple Block Execution API."""

import json
import logging
import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

from app.blocks import BLOCK_REGISTRY
from app.dependencies import block_instances, _create_block_instance, init_blocks
from app.routers import (
    auth,
    blocks,
    chain,
    chat,
    debug,
    execute,
    health,
    memory,
    monitoring,
    static,
    upload,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all blocks eagerly at startup to avoid race conditions."""
    await init_blocks()
    yield


app = FastAPI(
    title="Cerebrum Blocks",
    description="Build AI Like Lego - Simple Block Execution API",
    version="2.0.0",
    docs_url="/docs",
    lifespan=lifespan,
)

# CORS Origins - explicit list for cerebrum-platform frontend
CORS_ORIGINS = [
    "https://cerebrum-platform.onrender.com",
    "https://cerebrum-platform-j1zs.onrender.com",
    "https://cerebrum-store.onrender.com",
    "https://cerebrum-store-j1zs.onrender.com",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# CORS middleware — FastAPI echoes Access-Control-Request-Headers so no literal * is sent
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
    allow_credentials=True,
    max_age=86400,
)


# File upload security middleware
@app.middleware("http")
async def file_upload_security_middleware(request: Request, call_next):
    """Auto-validate file uploads on /ingest and /upload endpoints"""
    path = request.url.path.lower()

    if any(x in path for x in ["/ingest", "/upload", "/process-file", "/chain"]):
        body = await request.body()

        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        # Check if file-related
        if any(k in str(data) for k in ["file_path", "content", "filename", "file"]):
            if "security" not in block_instances:
                block_instances["security"] = _create_block_instance(BLOCK_REGISTRY["security"])
            security = block_instances["security"]
            if security:
                try:
                    validation = await security.validate_file(data, {})
                    if not validation.get("safe"):
                        return JSONResponse(
                            status_code=400,
                            content={
                                "status": "error",
                                "error": "Security validation failed",
                                "details": validation.get("error"),
                                "violation": validation.get("violation")
                            }
                        )
                except Exception:
                    pass

        # Rebuild request with original body
        async def receive():
            return {"type": "http.request", "body": body}

        request = Request(request.scope, receive, request._send)

    return await call_next(request)


# Include all routers
app.include_router(blocks.router)
app.include_router(execute.router)
app.include_router(chain.router)
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(auth.router)
app.include_router(memory.router)
app.include_router(monitoring.router)
app.include_router(health.router)
app.include_router(static.router)
app.include_router(debug.router)


# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
