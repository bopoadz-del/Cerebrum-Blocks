"""Cerebrum Store API - Block Marketplace"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

app = FastAPI(title="Cerebrum Store", description="Block Marketplace")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BLOCKS_DB = {}

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

@app.get("/health")
def health():
    return {"status": "healthy", "service": "store", "blocks": len(BLOCKS_DB)}

@app.get("/v1/blocks")
def list_blocks():
    return {"blocks": list(BLOCKS_DB.values()), "total": len(BLOCKS_DB)}

@app.get("/v1/blocks/{block_id}")
def get_block(block_id: str):
    return BLOCKS_DB.get(block_id, {"error": "Not found"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
