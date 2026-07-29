import os
import subprocess
from datetime import datetime, timezone
from fastapi import APIRouter

from app.blocks import BLOCK_REGISTRY
from app.dependencies import block_instances, MONITORING_AVAILABLE, get_monitoring_block

router = APIRouter()


def _probe_kimi_cli() -> dict:
    """Evaluated workbench capability: a registered block is not a capability
    unless the Kimi CLI actually answers."""
    probe = {"registered": "workbench" in BLOCK_REGISTRY, "cli_ok": False}
    cli = os.getenv("KIMI_CLI_PATH", "kimi").strip() or "kimi"
    try:
        proc = subprocess.run(
            [cli, "--version"], capture_output=True, text=True, timeout=5, check=False
        )
        probe["cli_ok"] = proc.returncode == 0
        if proc.returncode == 0:
            probe["cli_version"] = (proc.stdout or "").strip()[:80]
        else:
            probe["error"] = (proc.stderr or "").strip()[:200] or f"exit {proc.returncode}"
    except FileNotFoundError:
        probe["error"] = f"CLI not found: {cli}"
    except Exception as exc:  # noqa: BLE001 - health probes must not raise
        probe["error"] = str(exc)[:200]
    return probe


@router.get("/health")
def health():
    """Health check."""
    return {
        "status": "healthy",
        "blocks_loaded": len(block_instances),
        "blocks_available": len(BLOCK_REGISTRY),
        "kimi_workbench": _probe_kimi_cli(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/stats")
def stats():
    """Platform stats."""
    return {
        "blocks": [name for name in BLOCK_REGISTRY.keys() if not name.startswith("container_")],
        "total_blocks": len(BLOCK_REGISTRY),
        "version": "2.0.0",
    }


@router.get("/v1/health")
def health_v1():
    """Health check for Render (v1 API)."""
    return health()


@router.get("/v1/system/health")
async def full_health():
    """Complete system health with predictions."""
    if not MONITORING_AVAILABLE:
        return health_v1()
    block = get_monitoring_block()
    return await block.execute({"action": "health_report"})
