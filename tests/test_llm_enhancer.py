"""Tests for the LLM enhancer block.

These tests never hit the real Anthropic API. We exercise:

- ``is_active()`` returns False when ``ANTHROPIC_API_KEY`` is unset.
- ``is_active()`` returns False when the ``anthropic`` package is missing.
- The ``enhance_*`` methods return ``{"additions": [], "skipped": True,
  "reason": "..."}`` cleanly when no client can be built.
- With ``_anthropic_client`` monkeypatched to a fake whose
  ``messages.create`` returns a TextBlock-shaped response containing
  JSON additions, ``enhance_quantities`` parses them.
- Bad JSON from the model surfaces as ``{"additions": [], "error": "..."}``
  rather than raising.
- ``process()`` dispatches on ``params.action`` and errors on unknown.
"""

from __future__ import annotations

import sys
import types
from typing import Any, Dict, List

import pytest

from app.blocks.llm_enhancer import LLMEnhancerBlock


# ── helpers ────────────────────────────────────────────────────────────


class _FakeTextBlock:
    """Mimics anthropic.types.TextBlock — has a ``.text`` attribute."""

    def __init__(self, text: str) -> None:
        self.text = text


class _FakeMessage:
    """Mimics anthropic.types.Message — has a ``.content`` list."""

    def __init__(self, text: str) -> None:
        self.content = [_FakeTextBlock(text)]


class _FakeMessages:
    def __init__(self, payload_text: str, capture: List[Dict[str, Any]]) -> None:
        self._payload_text = payload_text
        self._capture = capture

    def create(self, **kwargs: Any) -> _FakeMessage:
        # Capture the call arguments so tests can inspect cache_control etc.
        self._capture.append(kwargs)
        return _FakeMessage(self._payload_text)


class _FakeAnthropic:
    def __init__(self, payload_text: str) -> None:
        self.calls: List[Dict[str, Any]] = []
        self.messages = _FakeMessages(payload_text, self.calls)


def _patch_client(monkeypatch: pytest.MonkeyPatch, fake: Any) -> None:
    """Replace the block's _anthropic_client with one returning ``fake``."""
    monkeypatch.setattr(
        LLMEnhancerBlock,
        "_anthropic_client",
        lambda self: fake,
    )


# ── is_active() ────────────────────────────────────────────────────────


def test_is_active_false_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    block = LLMEnhancerBlock()
    # Bypass any cached client from prior tests.
    if hasattr(block, "_client_cache"):
        delattr(block, "_client_cache")
    assert block.is_active() is False


def test_is_active_false_when_anthropic_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
    # Sentinel: simulate ImportError by setting the module entry to None.
    monkeypatch.setitem(sys.modules, "anthropic", None)
    block = LLMEnhancerBlock()
    if hasattr(block, "_client_cache"):
        delattr(block, "_client_cache")
    assert block.is_active() is False


# ── enhance_* short-circuits when client unavailable ───────────────────


@pytest.mark.asyncio
async def test_enhance_quantities_skipped_when_client_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_client(monkeypatch, None)
    block = LLMEnhancerBlock()
    out = await block.enhance_quantities("some text", {})
    assert out == {"additions": [], "skipped": True, "reason": "client_unavailable"}


@pytest.mark.asyncio
async def test_enhance_risks_skipped_when_client_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_client(monkeypatch, None)
    block = LLMEnhancerBlock()
    out = await block.enhance_risks("some text", [])
    assert out == {"additions": [], "skipped": True, "reason": "client_unavailable"}


@pytest.mark.asyncio
async def test_enhance_rfis_skipped_when_client_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_client(monkeypatch, None)
    block = LLMEnhancerBlock()
    out = await block.enhance_rfis("some text", [])
    assert out == {"additions": [], "skipped": True, "reason": "client_unavailable"}


# ── happy path with a fake client ──────────────────────────────────────


@pytest.mark.asyncio
async def test_enhance_quantities_parses_additions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = (
        '{"additions": ['
        '{"item": "switchgear_400v", "quantity": 6, "unit": "ea", '
        '"category": "electrical", "source_quote": "400V switchgear: 6 ea"}'
        "]}"
    )
    fake = _FakeAnthropic(payload)
    _patch_client(monkeypatch, fake)

    block = LLMEnhancerBlock()
    out = await block.enhance_quantities(
        "Document text mentioning 400V switchgear: 6 ea",
        {"floor_area_m2": {"quantity": 1000, "unit": "m2"}},
    )

    assert out.get("additions"), "expected at least one parsed addition"
    assert out["additions"][0]["item"] == "switchgear_400v"
    assert out["additions"][0]["quantity"] == 6
    assert out["additions"][0]["unit"] == "ea"

    # Verify the call shape: prompt caching marker on the system block,
    # max_tokens cap honoured, user message contains BASELINE + DOCUMENT TEXT.
    assert len(fake.calls) == 1
    call = fake.calls[0]
    assert isinstance(call.get("system"), list)
    assert call["system"][0].get("cache_control") == {"type": "ephemeral"}
    assert call.get("max_tokens") == 4000
    user_content = call["messages"][0]["content"]
    assert "BASELINE:" in user_content
    assert "DOCUMENT TEXT:" in user_content


@pytest.mark.asyncio
async def test_enhance_quantities_handles_bad_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeAnthropic("this is not JSON at all, just prose")
    _patch_client(monkeypatch, fake)

    block = LLMEnhancerBlock()
    out = await block.enhance_quantities("some doc text", {})

    assert out["additions"] == []
    assert "error" in out
    assert "json_parse_failed" in out["error"]
    # Critically: no exception was raised.


@pytest.mark.asyncio
async def test_enhance_rfis_filters_short_questions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = (
        '{"additions": ['
        '{"category": "clarification", "subject": "Beam size", '
        '"question": "What is the steel grade for the W14x90 beams on level 3?", '
        '"discipline": "Structural", "severity": "medium", '
        '"source_quote": "W14x90 beams TBD"},'
        '{"category": "clarification", "subject": "TBD", '
        '"question": "TBD", "discipline": "Architecture", '
        '"severity": "low", "source_quote": "TBD"}'
        "]}"
    )
    fake = _FakeAnthropic(payload)
    _patch_client(monkeypatch, fake)

    block = LLMEnhancerBlock()
    out = await block.enhance_rfis("text mentioning W14x90 beams TBD", [])

    # The short / trigger-word RFI must be filtered out.
    assert len(out["additions"]) == 1
    assert "steel grade" in out["additions"][0]["question"]


# ── process() dispatch ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_process_status_action_reports_inactive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    block = LLMEnhancerBlock()
    if hasattr(block, "_client_cache"):
        delattr(block, "_client_cache")

    out = await block.process({}, {"action": "status"})
    assert out["status"] == "success"
    assert out["is_active"] is False
    assert out["model"]


@pytest.mark.asyncio
async def test_process_status_action_reports_active(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeAnthropic('{"additions": []}')
    _patch_client(monkeypatch, fake)

    block = LLMEnhancerBlock()
    out = await block.process({}, {"action": "status"})
    assert out["status"] == "success"
    assert out["is_active"] is True


@pytest.mark.asyncio
async def test_process_dispatches_enhance_quantities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeAnthropic(
        '{"additions": [{"item": "rebar_20mm", "quantity": 1500, '
        '"unit": "kg", "category": "concrete", '
        '"source_quote": "20mm rebar: 1500 kg"}]}'
    )
    _patch_client(monkeypatch, fake)

    block = LLMEnhancerBlock()
    out = await block.process(
        {"text": "doc...", "baseline": {}},
        {"action": "enhance_quantities"},
    )
    assert out["status"] == "success"
    assert out["additions"][0]["item"] == "rebar_20mm"


@pytest.mark.asyncio
async def test_process_dispatches_enhance_risks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeAnthropic('{"additions": []}')
    _patch_client(monkeypatch, fake)

    block = LLMEnhancerBlock()
    out = await block.process(
        {"text": "doc...", "baseline": []},
        {"action": "enhance_risks"},
    )
    assert out["status"] == "success"
    assert out["additions"] == []


@pytest.mark.asyncio
async def test_process_dispatches_enhance_rfis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeAnthropic('{"additions": []}')
    _patch_client(monkeypatch, fake)

    block = LLMEnhancerBlock()
    out = await block.process(
        {"text": "doc...", "baseline": []},
        {"action": "enhance_rfis"},
    )
    assert out["status"] == "success"
    assert out["additions"] == []


@pytest.mark.asyncio
async def test_process_unknown_action_errors() -> None:
    block = LLMEnhancerBlock()
    out = await block.process({}, {"action": "do_something_undefined"})
    assert out["status"] == "error"
    assert "Unknown action" in out["error"]
