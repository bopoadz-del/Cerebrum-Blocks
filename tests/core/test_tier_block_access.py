"""The tier block-access boundary must be enforced server-side on /v1/execute."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.routers.execute import ExecuteRequest, _run_block


class _EchoBlock:
    async def execute(self, input_data, params):
        return {
            "block": "x",
            "request_id": "t",
            "status": "success",
            "result": {"ok": True},
            "confidence": 1.0,
            "source_id": "x-t",
            "metadata": {},
            "processing_time_ms": 0,
        }


def _patches(names):
    echo = _EchoBlock()
    return [
        patch("app.routers.execute.BLOCK_REGISTRY", {n: object for n in names}),
        patch("app.routers.execute.get_block_instance", lambda n: echo),
        patch("app.routers.execute.adapt_input", lambda d, b: d),
    ]


async def _run(block, tier):
    auth = {"id": "k", "email": "t@example.com", "tier": tier}
    ps = _patches([block])
    for p in ps:
        p.start()
    try:
        return await _run_block(ExecuteRequest(block=block, input={"text": "hi"}, params={}), auth)
    finally:
        for p in ps:
            p.stop()


@pytest.mark.asyncio
async def test_free_tier_can_use_trial_blocks():
    response = await _run("knowledge", "free")
    assert response["result"]["ok"] is True


@pytest.mark.asyncio
async def test_free_tier_denied_outside_allowed_list():
    with pytest.raises(HTTPException) as exc:
        await _run("construction_v2", "free")
    assert exc.value.status_code == 403
    assert "tier" in str(exc.value.detail).lower()


@pytest.mark.asyncio
async def test_pro_tier_unrestricted():
    response = await _run("construction_v2", "pro")
    assert response["result"]["ok"] is True
