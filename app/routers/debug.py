import os

from fastapi import APIRouter

router = APIRouter()


@router.get("/debug/env")
def debug_env():
    """Debug endpoint to check environment variables (remove in production)"""
    return {
        "deepseek_key_set": bool(os.getenv("DEEPSEEK_API_KEY")),
        "deepseek_key_prefix": os.getenv("DEEPSEEK_API_KEY", "")[:10] if os.getenv("DEEPSEEK_API_KEY") else None,
        "environment": os.getenv("ENV", "unknown"),
        "data_dir": os.getenv("DATA_DIR", "not_set")
    }


@router.get("/v1/debug/env")
def debug_env_v1():
    """Debug endpoint (v1 alias)."""
    return debug_env()
