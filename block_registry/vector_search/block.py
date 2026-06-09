#!/usr/bin/env python3
"""
Auto-generated adapter for Cerebrum block: vector_search
Wraps app.blocks.vector_search.VectorSearchBlock.process() into a synchronous run() function.
"""

import sys
import asyncio

sys.path.insert(0, "/app")

from app.blocks import BLOCK_REGISTRY


def run(**kwargs):
    """
    Execute the vector_search block.
    Accepts keyword args matching the block's inputs/params.
    Returns the block's raw result dict.
    """
    block_cls = BLOCK_REGISTRY["vector_search"]
    instance = block_cls()

    # Separate input from params
    input_data = kwargs.get("input", kwargs)
    params = {k: v for k, v in kwargs.items() if k != "input"}

    # process() is async — run it in a new event loop
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        # Already inside an async context (e.g. FastAPI) — schedule it
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, instance.process(input_data, params))
            return future.result()
    else:
        return asyncio.run(instance.process(input_data, params))
