from typing import Optional

from fastapi import APIRouter, HTTPException

from app.dependencies import AUTH_AVAILABLE, get_auth_block

router = APIRouter()


@router.post("/v1/auth/validate")
async def validate_key(request: dict):
    """Validate an API key"""
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Auth not available")
    block = get_auth_block()
    return await block.execute({"action": "validate", "key": request.get("key")})


@router.post("/v1/auth/keys")
async def create_key(request: dict):
    """Create a new API key (admin only)"""
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Auth not available")
    block = get_auth_block()
    return await block.execute({"action": "create_key", **request})


@router.get("/v1/auth/keys")
async def list_keys(admin_key: str):
    """List all API keys (admin only)"""
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Auth not available")
    block = get_auth_block()
    return await block.execute({"action": "list_keys", "admin_key": admin_key})


@router.post("/v1/auth/keys/revoke")
async def revoke_key(request: dict):
    """Revoke an API key"""
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Auth not available")
    block = get_auth_block()
    return await block.execute({"action": "revoke_key", **request})


@router.post("/v1/auth/keys/rotate")
async def rotate_key(request: dict):
    """Rotate an API key"""
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Auth not available")
    block = get_auth_block()
    return await block.execute({"action": "rotate_key", **request})


@router.post("/v1/auth/check")
async def check_permission(request: dict):
    """Check if key has a permission"""
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Auth not available")
    block = get_auth_block()
    return await block.execute({"action": "check_permission", **request})


@router.get("/v1/auth/usage")
async def get_usage(key: str, admin_key: Optional[str] = None):
    """Get usage stats for a key"""
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Auth not available")
    block = get_auth_block()
    return await block.execute({"action": "get_usage", "key": key, "admin_key": admin_key})
