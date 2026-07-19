"""Tests for the scope_extractor block."""

from __future__ import annotations

import pytest

from app.blocks.scope_extractor import ScopeExtractorBlock


@pytest.mark.asyncio
async def test_scope_extractor_accepts_brief():
    block = ScopeExtractorBlock()
    result = await block.process({"brief": "Build a warehouse in 12 months"})
    assert isinstance(result, dict)
    assert "status" in result


@pytest.mark.asyncio
async def test_scope_extractor_requires_no_file():
    block = ScopeExtractorBlock()
    result = await block.process({"text": "Small office fit-out"})
    assert isinstance(result, dict)
    assert "status" in result
