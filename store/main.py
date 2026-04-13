"""Cerebrum Store API - Block Marketplace"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

from app.containers.security import SecurityContainer

app = FastAPI(title="Cerebrum Store", description="Block Marketplace")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BLOCKS_DB = {}

# Lazy-init security container
_security_container = None

def get_security():
    global _security_container
    if _security_container is None:
        _security_container = SecurityContainer()
    return _security_container


def init_catalog():
    sample = [
        {"id": "blk_construction", "name": "construction", "displayName": "Construction AI", 
         "description": "BIM processing, PDF extraction", "category": "Domain Containers",
         "tags": ["aec", "bim"], "icon": "🏗️", "price": 299, "author": "Cerebrum", 
         "rating": 4.8, "reviews": 42},
        {"id": "blk_medical", "name": "medical", "displayName": "Medical AI",
         "description": "HIPAA-compliant DICOM processing", "category": "Domain Containers",
         "tags": ["healthcare", "hipaa"], "icon": "🏥", "price": 499, "author": "Cerebrum",
         "rating": 4.9, "reviews": 28},
        {"id": "blk_chat", "name": "chat", "displayName": "Chat AI",
         "description": "Multi-provider LLM", "category": "AI Core",
         "tags": ["ai", "llm"], "icon": "💬", "price": 49, "author": "Cerebrum",
         "rating": 4.9, "reviews": 156},
    ]
    for b in sample:
        BLOCKS_DB[b["id"]] = b

init_catalog()

async def save_block_to_catalog(block_data: dict):
    block_id = block_data.get("id") or f"blk_{block_data.get('name', 'unknown')}"
    block_data["id"] = block_id
    BLOCKS_DB[block_id] = block_data
    return {"status": "published", "block_id": block_id}

async def update_block_in_catalog(block_id: str, block_data: dict):
    if block_id not in BLOCKS_DB:
        raise HTTPException(status_code=404, detail="Block not found")
    BLOCKS_DB[block_id].update(block_data)
    return {"status": "updated", "block_id": block_id}

async def audit_log(event_type: str, details: dict):
    security = get_security()
    await security.audit({
        "action": event_type,
        "result": details,
        "user": "store_api"
    })
    return True


@app.get("/health")
def health():
    return {"status": "healthy", "service": "store", "blocks": len(BLOCKS_DB)}

@app.get("/v1/blocks")
def list_blocks():
    return {"blocks": list(BLOCKS_DB.values()), "total": len(BLOCKS_DB)}

@app.get("/v1/blocks/{block_id}")
def get_block(block_id: str):
    return BLOCKS_DB.get(block_id, {"error": "Not found"})


@app.post("/v1/blocks/publish")
async def publish_block(block_data: dict):
    """Publish new block with security scanning"""
    security = get_security()
    
    # Validate block code before accepting
    if block_data.get("code"):
        validation = await security.validate_block_code(
            {
                "code": block_data.get("code"),
                "block_name": block_data.get("name", "unnamed"),
                "language": block_data.get("language", "python")
            },
            {}
        )
        
        if not validation.get("safe"):
            # Log security attempt
            await audit_log("BLOCK_REJECTED", {
                "block": block_data.get("name"),
                "reason": validation.get("violation"),
                "severity": validation.get("severity"),
                "violations": validation.get("violations_count")
            })
            
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Block rejected by security scan",
                    "details": validation.get("error"),
                    "violations": validation.get("violations")
                }
            )
        
        # Add security metadata to block record
        block_data["security_scan"] = {
            "passed": True,
            "hash": validation.get("code_hash"),
            "lines": validation.get("lines_of_code"),
            "scanned_at": datetime.utcnow().isoformat()
        }
        
        # Log successful submission
        await security.audit_block_submission(
            block_data.get("name", "unnamed"),
            validation,
            block_data.get("author", "unknown")
        )
    
    # Continue with normal publish logic
    return await save_block_to_catalog(block_data)


@app.post("/v1/blocks/update/{block_id}")
async def update_block(block_id: str, block_data: dict):
    """Update existing block with re-validation"""
    # Re-scan on any code update
    if block_data.get("code"):
        security = get_security()
        validation = await security.validate_block_code(
            {
                "code": block_data.get("code"),
                "block_name": block_id,
                "language": block_data.get("language", "python")
            },
            {}
        )
        
        if not validation.get("safe"):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Updated block failed security scan",
                    "violations": validation.get("violations")
                }
            )
        
        block_data["security_scan"] = {
            "passed": True,
            "hash": validation.get("code_hash"),
            "lines": validation.get("lines_of_code"),
            "scanned_at": datetime.utcnow().isoformat()
        }
    
    return await update_block_in_catalog(block_id, block_data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
