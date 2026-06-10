"""Shared dependencies and block instance management for FastAPI app."""

import asyncio
import inspect
import logging
import os
import sys
from typing import Any, Dict, Optional

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.blocks import BLOCK_REGISTRY
from app.core.auth import auth as auth_manager

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# HAL initialization
try:
    from blocks.hal.src.detector import HALBlock
    _hal = HALBlock()

    def get_hal_block():
        # Exposed via the same accessor pattern memory/monitoring/auth use,
        # so _resolve_dep("hal") finds it for blocks declaring requires=["hal"]
        # (config.py is the main one).
        return _hal

    HAL_AVAILABLE = True
except Exception as e:
    logger.warning("HALBlock not available during startup: %s", e)
    _hal = None
    get_hal_block = None  # type: ignore[assignment]
    HAL_AVAILABLE = False

# Shared block instances
block_instances: Dict[str, Any] = {}


def _create_block_instance(block_class):
    """Create block instance with proper arguments."""
    sig = inspect.signature(block_class.__init__)
    params = list(sig.parameters.keys())

    if "hal_block" in params and "config" in params:
        instance = block_class(hal_block=_hal, config={})
    else:
        instance = block_class()

    if hasattr(instance, "set_platform"):
        try:
            instance.set_platform(BLOCK_REGISTRY, block_instances, _create_block_instance, get_memory_block)
        except Exception:
            pass

    return instance


def _resolve_dep(dep_name: str):
    """Look up a dep instance via four sources, in order:

    1. block_instances (already wired)
    2. BLOCK_REGISTRY (lazy-instantiate via get_block_instance)
    3. Legacy accessor `get_<name>_block()` (memory/monitoring/auth live here)
    4. Globals — caches like `_memory_block` set by the legacy accessors

    Returns the instance, or None if no source has it. None is fine — most
    dependent blocks check `if self.X_block:` before using the dep, and the
    audit caught the few that didn't.
    """
    if dep_name in block_instances:
        return block_instances[dep_name]
    if dep_name in BLOCK_REGISTRY:
        try:
            return get_block_instance(dep_name)
        except Exception:
            logger.warning("dep_resolver: %s in BLOCK_REGISTRY but failed to instantiate", dep_name)
    accessor = globals().get(f"get_{dep_name}_block")
    if callable(accessor):
        try:
            return accessor()
        except Exception:
            logger.warning("dep_resolver: legacy accessor get_%s_block failed", dep_name)
    cached = globals().get(f"_{dep_name}_block")
    if cached is not None:
        return cached
    return None


def _wire_block_dependencies(instance, block_class, name: str = None):
    """Wire requires=[] dependencies into a platform block instance.

    The audit found 31 blocks with requires=["config"|"database"|"memory"|...]
    where the dep name isn't in BLOCK_REGISTRY. Previous version silently
    skipped — the block then crashed on first use of self.X_block. Now we
    resolve via four sources (registry → lazy instance → legacy accessor →
    cached global) and only skip + log when none has it.
    """
    requires = getattr(block_class, "requires", []) or []
    for dep_name in requires:
        dep_instance = _resolve_dep(dep_name)
        if dep_instance is None:
            logger.warning(
                "block %s requires '%s' but no provider found "
                "(not in BLOCK_REGISTRY, no get_%s_block accessor) — "
                "block will run without it; calls that touch self.%s_block may fail.",
                name or "?", dep_name, dep_name, dep_name,
            )
            continue
        if hasattr(instance, "wire"):
            instance.wire(dep_name, dep_instance)
        elif hasattr(instance, "inject"):
            instance.inject(dep_name, dep_instance)
        else:
            setattr(instance, f"{dep_name}_block", dep_instance)


def get_block_instance(block_name: str) -> Any:
    if block_name not in block_instances:
        block_class = BLOCK_REGISTRY[block_name]
        block_instances[block_name] = _create_block_instance(block_class)
        _wire_block_dependencies(block_instances[block_name], block_class, block_name)
    return block_instances[block_name]


# Memory block
_memory_block = None

try:
    from blocks.memory.src.block import MemoryBlock

    def get_memory_block():
        global _memory_block
        if _memory_block is None:
            _memory_block = MemoryBlock(None, {"max_size": 10000, "default_ttl": 3600})
            asyncio.create_task(_memory_block.initialize())
        return _memory_block

    MEMORY_AVAILABLE = True
except Exception as e:
    MEMORY_AVAILABLE = False
    get_memory_block = None  # type: ignore[assignment]
    logger.warning("Memory block not available: %s", e)


# Monitoring block
_monitoring_block = None

try:
    from blocks.monitoring.src.block import MonitoringBlock

    def get_monitoring_block():
        global _monitoring_block
        if _monitoring_block is None:
            _monitoring_block = MonitoringBlock(None, {})
            _monitoring_block.memory_block = get_memory_block()
            asyncio.create_task(_monitoring_block.initialize())
        return _monitoring_block

    MONITORING_AVAILABLE = True
except Exception as e:
    MONITORING_AVAILABLE = False
    get_monitoring_block = None  # type: ignore[assignment]
    logger.warning("Monitoring block not available: %s", e)


# Auth block
_auth_block = None

try:
    from blocks.auth.src.block import AuthBlock

    def get_auth_block():
        global _auth_block
        if _auth_block is None:
            _auth_block = AuthBlock(None, {
                "rate_limit_default": 100,
                "rate_limit_window": 60,
                "master_key": os.getenv("CEREBRUM_MASTER_KEY"),
            })
            _auth_block.memory_block = get_memory_block()
            asyncio.create_task(_auth_block.initialize())
        return _auth_block

    AUTH_AVAILABLE = True
except Exception as e:
    AUTH_AVAILABLE = False
    get_auth_block = None  # type: ignore[assignment]
    logger.warning("Auth block not available: %s", e)


security = HTTPBearer(auto_error=False)


async def require_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """Require valid API key for protected endpoints"""
    return auth_manager.validate_key(credentials)


async def init_blocks():
    """Lazy-only initialisation — pre-warm runs in a thread pool.

    Earlier we pre-warmed core blocks here (chat/pdf/ocr/construction/zvec/
    smart_orchestrator/skills) which pulls in sklearn/sympy/ezdxf etc.
    Even as a background asyncio task, those synchronous imports BLOCK
    THE EVENT LOOP. Render's health checker then times out hitting
    /health, marks the worker unhealthy, and kills it — visible in the
    service event log as `server_failed` with `dial tcp: connect: ...`.

    Now: pre-warm runs in a thread executor so the event loop stays
    responsive throughout. /health responds instantly during the pre-warm
    window. First /v1/execute on a not-yet-warm block pays a small lazy-
    import cost (~50–500ms depending on the block).

    Override via env:
        BLOCKS_PREWARM=none → skip pre-warm entirely (pure lazy)
        BLOCKS_PREWARM=all  → pre-warm every registered block (benchmark)
        BLOCKS_PREWARM=core → default; pre-warm SPA happy-path blocks
    """
    prewarm_mode = os.getenv("BLOCKS_PREWARM", "core").strip().lower()
    if prewarm_mode == "none":
        return

    if prewarm_mode == "all":
        targets = list(BLOCK_REGISTRY.keys())
    else:
        targets = [
            "chat", "pdf", "ocr", "zvec", "skills",
        ]

    def _warm_target(name: str) -> None:
        if name in block_instances:
            return
        try:
            block_class = BLOCK_REGISTRY[name]
            block_instances[name] = _create_block_instance(block_class)
        except Exception as e:
            logger.warning("Failed to initialise block %s: %s", name, e)

    loop = asyncio.get_running_loop()
    for name in targets:
        # to_thread() runs the synchronous import in the default executor —
        # event loop continues serving /health and other fast endpoints.
        await asyncio.to_thread(_warm_target, name)

    # Wire deps for whatever we did manage to instantiate (cheap, no imports)
    for name, instance in list(block_instances.items()):
        block_class = BLOCK_REGISTRY.get(name)
        if block_class:
            _wire_block_dependencies(instance, block_class, name)

    # The legacy accessors below internally call asyncio.create_task(...)
    # which REQUIRES a running event loop — must be invoked from the loop,
    # not via to_thread. Their imports already happened above; this is just
    # the instance creation, which is cheap.
    if get_memory_block:
        try: get_memory_block()
        except Exception: logger.exception("get_memory_block init failed")
    if get_monitoring_block:
        try: get_monitoring_block()
        except Exception: logger.exception("get_monitoring_block init failed")
    if get_auth_block:
        try: get_auth_block()
        except Exception: logger.exception("get_auth_block init failed")

    try:
        if "smart_orchestrator" in block_instances and "skills" in block_instances:
            orch = block_instances["smart_orchestrator"]
            skills = block_instances["skills"]
            if hasattr(orch, "wire_skills"):
                orch.wire_skills(skills)
    except Exception as e:
        logger.warning("Failed to wire skills into smart_orchestrator: %s", e)
