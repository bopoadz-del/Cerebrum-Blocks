"""
Cerebrum Store API - Block Marketplace Backend

Completely separate from Platform API.
Handles: Catalog, Shopping, Pricing, Billing, Creator Payouts
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
import json
import os

app = FastAPI(
    title="Cerebrum Store",
    description="Block Marketplace - Browse, Buy, and Sell AI Blocks",
    version="1.0.0"
)

# CORS - Allow all storefronts
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory databases (use PostgreSQL in production)
BLOCKS_DB = {}
CARTS_DB = {}
ORDERS_DB = {}
USERS_DB = {}

# -------------------- BLOCK CATALOG --------------------

class BlockListing(BaseModel):
    id: str
    name: str
    display_name: str
    description: str
    category: str
    tags: List[str]
    icon: str
    price_monthly: float
    price_per_use: Optional[float] = None
    author: str
    author_id: str
    rating: float = 4.5
    reviews_count: int = 0
    installs: int = 0
    layer: int = 3
    created_at: str
    updated_at: str
    status: str = "active"  # active, pending, suspended

# Initialize with sample blocks
def init_catalog():
    sample_blocks = [
        {
            "id": "blk_construction",
            "name": "construction",
            "display_name": "Construction AI",
            "description": "BIM processing, PDF extraction, QA inspection for AEC industry",
            "category": "Domain Containers",
            "tags": ["aec", "bim", "construction", "pdf"],
            "icon": "🏗️",
            "price_monthly": 299.0,
            "price_per_use": 5.0,
            "author": "Cerebrum",
            "author_id": "usr_cerebrum",
            "rating": 4.8,
            "reviews_count": 42,
            "installs": 156,
            "layer": 3,
            "created_at": "2026-01-15T00:00:00Z",
            "updated_at": "2026-04-01T00:00:00Z",
            "status": "active"
        },
        {
            "id": "blk_medical",
            "name": "medical",
            "display_name": "Medical AI",
            "description": "HIPAA-compliant DICOM processing, medical image analysis",
            "category": "Domain Containers",
            "tags": ["healthcare", "hipaa", "dicom", "medical"],
            "icon": "🏥",
            "price_monthly": 499.0,
            "author": "Cerebrum",
            "author_id": "usr_cerebrum",
            "rating": 4.9,
            "reviews_count": 28,
            "installs": 89,
            "layer": 3,
            "created_at": "2026-02-01T00:00:00Z",
            "updated_at": "2026-04-01T00:00:00Z",
            "status": "active"
        },
        {
            "id": "blk_chat",
            "name": "chat",
            "display_name": "Chat AI",
            "description": "Multi-provider LLM with DeepSeek, Groq, OpenAI support",
            "category": "AI Core",
            "tags": ["ai", "llm", "chat", "deepseek", "openai"],
            "icon": "💬",
            "price_monthly": 49.0,
            "price_per_use": 0.01,
            "author": "Cerebrum",
            "author_id": "usr_cerebrum",
            "rating": 4.9,
            "reviews_count": 156,
            "installs": 1250,
            "layer": 2,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-04-01T00:00:00Z",
            "status": "active"
        },
        {
            "id": "blk_pdf",
            "name": "pdf",
            "display_name": "PDF Processor",
            "description": "Extract text, tables, images from PDF files",
            "category": "Documents",
            "tags": ["pdf", "documents", "extraction", "ocr"],
            "icon": "📄",
            "price_monthly": 29.0,
            "price_per_use": 0.05,
            "author": "Cerebrum",
            "author_id": "usr_cerebrum",
            "rating": 4.6,
            "reviews_count": 112,
            "installs": 890,
            "layer": 3,
            "created_at": "2026-01-10T00:00:00Z",
            "updated_at": "2026-04-01T00:00:00Z",
            "status": "active"
        },
        {
            "id": "blk_ocr",
            "name": "ocr",
            "display_name": "OCR Vision",
            "description": "Text extraction from images and scanned documents",
            "category": "Documents",
            "tags": ["ocr", "vision", "documents", "image"],
            "icon": "👁️",
            "price_monthly": 29.0,
            "price_per_use": 0.03,
            "author": "Cerebrum",
            "author_id": "usr_cerebrum",
            "rating": 4.5,
            "reviews_count": 89,
            "installs": 567,
            "layer": 3,
            "created_at": "2026-01-12T00:00:00Z",
            "updated_at": "2026-04-01T00:00:00Z",
            "status": "active"
        },
    ]
    
    for block in sample_blocks:
        BLOCKS_DB[block["id"]] = block

init_catalog()

@app.get("/health")
def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "store",
        "blocks_in_catalog": len(BLOCKS_DB),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/v1/blocks")
def list_blocks(
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "popular"  # popular, newest, price_low, price_high, rating
):
    """List all blocks in the store"""
    blocks = list(BLOCKS_DB.values())
    
    # Filter by category
    if category:
        blocks = [b for b in blocks if b["category"] == category]
    
    # Search
    if search:
        search = search.lower()
        blocks = [
            b for b in blocks 
            if search in b["name"].lower() 
            or search in b["description"].lower()
            or any(search in t.lower() for t in b["tags"])
        ]
    
    # Sort
    if sort_by == "popular":
        blocks.sort(key=lambda x: x["installs"], reverse=True)
    elif sort_by == "newest":
        blocks.sort(key=lambda x: x["created_at"], reverse=True)
    elif sort_by == "price_low":
        blocks.sort(key=lambda x: x["price_monthly"])
    elif sort_by == "price_high":
        blocks.sort(key=lambda x: x["price_monthly"], reverse=True)
    elif sort_by == "rating":
        blocks.sort(key=lambda x: x["rating"], reverse=True)
    
    return {
        "blocks": blocks,
        "total": len(blocks),
        "categories": list(set(b["category"] for b in BLOCKS_DB.values()))
    }

@app.get("/v1/blocks/{block_id}")
def get_block(block_id: str):
    """Get single block details"""
    if block_id not in BLOCKS_DB:
        raise HTTPException(404, "Block not found")
    return BLOCKS_DB[block_id]

# -------------------- SHOPPING CART --------------------

class CartItem(BaseModel):
    block_id: str
    plan: str = "monthly"  # monthly, per_use
    quantity: int = 1

class Cart(BaseModel):
    user_id: str
    items: List[CartItem]
    total_monthly: float = 0
    total_per_use: float = 0
    lego_tax: float = 0  # 20% platform fee
    creator_payout: float = 0  # 80% to creators

@app.get("/v1/cart/{user_id}")
def get_cart(user_id: str):
    """Get user's cart"""
    if user_id not in CARTS_DB:
        return {
            "user_id": user_id,
            "items": [],
            "total_monthly": 0,
            "total_per_use": 0,
            "subtotal": 0,
            "lego_tax": 0,
            "total": 0
        }
    return CARTS_DB[user_id]

@app.post("/v1/cart/{user_id}/add")
def add_to_cart(user_id: str, item: CartItem):
    """Add block to cart"""
    if user_id not in CARTS_DB:
        CARTS_DB[user_id] = {
            "user_id": user_id,
            "items": [],
            "total_monthly": 0,
            "total_per_use": 0,
            "subtotal": 0,
            "lego_tax": 0,
            "total": 0
        }
    
    # Check if block exists
    if item.block_id not in BLOCKS_DB:
        raise HTTPException(404, "Block not found")
    
    block = BLOCKS_DB[item.block_id]
    
    # Add to cart
    CARTS_DB[user_id]["items"].append({
        "block_id": item.block_id,
        "block_name": block["name"],
        "block_display_name": block["display_name"],
        "icon": block["icon"],
        "plan": item.plan,
        "price": block["price_monthly"] if item.plan == "monthly" else block.get("price_per_use", 0),
        "quantity": item.quantity
    })
    
    # Recalculate totals
    cart = CARTS_DB[user_id]
    cart["total_monthly"] = sum(
        i["price"] * i["quantity"] 
        for i in cart["items"] 
        if i["plan"] == "monthly"
    )
    cart["total_per_use"] = sum(
        i["price"] * i["quantity"] 
        for i in cart["items"] 
        if i["plan"] == "per_use"
    )
    cart["subtotal"] = cart["total_monthly"]
    cart["lego_tax"] = cart["subtotal"] * 0.20  # 20% platform fee
    cart["creator_payout"] = cart["subtotal"] * 0.80  # 80% to creators
    cart["total"] = cart["subtotal"] + cart["lego_tax"]
    
    return cart

@app.delete("/v1/cart/{user_id}/remove/{block_id}")
def remove_from_cart(user_id: str, block_id: str):
    """Remove block from cart"""
    if user_id not in CARTS_DB:
        raise HTTPException(404, "Cart not found")
    
    CARTS_DB[user_id]["items"] = [
        i for i in CARTS_DB[user_id]["items"] 
        if i["block_id"] != block_id
    ]
    
    # Recalculate
    cart = CARTS_DB[user_id]
    cart["total_monthly"] = sum(i["price"] * i["quantity"] for i in cart["items"] if i["plan"] == "monthly")
    cart["subtotal"] = cart["total_monthly"]
    cart["lego_tax"] = cart["subtotal"] * 0.20
    cart["creator_payout"] = cart["subtotal"] * 0.80
    cart["total"] = cart["subtotal"] + cart["lego_tax"]
    
    return cart

# -------------------- CHECKOUT --------------------

@app.post("/v1/checkout/{user_id}")
def checkout(user_id: str):
    """Process checkout"""
    if user_id not in CARTS_DB or not CARTS_DB[user_id]["items"]:
        raise HTTPException(400, "Cart is empty")
    
    cart = CARTS_DB[user_id]
    order_id = f"ord_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    order = {
        "order_id": order_id,
        "user_id": user_id,
        "items": cart["items"],
        "subtotal": cart["subtotal"],
        "lego_tax": cart["lego_tax"],
        "creator_payout": cart["creator_payout"],
        "total": cart["total"],
        "status": "completed",
        "created_at": datetime.utcnow().isoformat()
    }
    
    ORDERS_DB[order_id] = order
    
    # Clear cart
    CARTS_DB[user_id] = {
        "user_id": user_id,
        "items": [],
        "total_monthly": 0,
        "total_per_use": 0,
        "subtotal": 0,
        "lego_tax": 0,
        "total": 0
    }
    
    return order

@app.get("/v1/orders/{user_id}")
def list_orders(user_id: str):
    """List user's orders"""
    orders = [o for o in ORDERS_DB.values() if o["user_id"] == user_id]
    return {"orders": orders, "total": len(orders)}

# -------------------- CREATOR API --------------------

@app.post("/v1/blocks/submit")
def submit_block(block: BlockListing):
    """Submit new block to store (pending review)"""
    block_id = f"blk_{block.name.lower().replace(' ', '_')}"
    
    if block_id in BLOCKS_DB:
        raise HTTPException(400, "Block already exists")
    
    new_block = block.dict()
    new_block["id"] = block_id
    new_block["status"] = "pending"
    new_block["created_at"] = datetime.utcnow().isoformat()
    new_block["updated_at"] = datetime.utcnow().isoformat()
    new_block["installs"] = 0
    new_block["reviews_count"] = 0
    new_block["rating"] = 0
    
    BLOCKS_DB[block_id] = new_block
    
    return {
        "message": "Block submitted for review",
        "block_id": block_id,
        "status": "pending"
    }

@app.get("/v1/creator/{creator_id}/earnings")
def creator_earnings(creator_id: str):
    """Get creator earnings"""
    # Calculate earnings from orders
    creator_blocks = [b for b in BLOCKS_DB.values() if b["author_id"] == creator_id]
    
    total_earnings = 0
    for order in ORDERS_DB.values():
        for item in order["items"]:
            block = BLOCKS_DB.get(item["block_id"])
            if block and block["author_id"] == creator_id:
                total_earnings += item["price"] * item["quantity"] * 0.80  # 80% payout
    
    return {
        "creator_id": creator_id,
        "total_earnings": round(total_earnings, 2),
        "blocks_published": len(creator_blocks),
        "total_installs": sum(b["installs"] for b in creator_blocks)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
