#!/usr/bin/env python3
"""
Auto-generated adapter for Cerebrum block: discovery
Wraps app.blocks.discovery.DiscoveryBlock.execute() into a synchronous run() function.
"""

import sys
import asyncio

sys.path.insert(0, "/app")

from app.blocks import BLOCK_REGISTRY


def _run_async(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return pool.submit(asyncio.run, coro).result()


def run(**kwargs):
    """
    Execute the discovery block.
    Accepts keyword args matching the block's inputs/params.
    Returns the standardized block result payload.
    """
    block_cls = BLOCK_REGISTRY["discovery"]
    instance = block_cls()

    input_data = kwargs.get("input", kwargs)
    params = {k: v for k, v in kwargs.items() if k != "input"}

    envelope = _run_async(instance.execute(input_data, params))
    if envelope.get("status") == "error":
        inner = envelope.get("result", {})
        message = inner.get("error") if isinstance(inner, dict) else str(inner)
        raise RuntimeError(message or f"discovery block failed")

    return envelope.get("result", envelope)
