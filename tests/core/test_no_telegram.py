"""Telegram is removed from the platform. It must stay removed.

Owner directive (2026-08-02, after repeated prior requests): no Telegram
bot, no Telegram channel, no Telegram integration anywhere. Previous
removals were partial — the bot was moved into ``block_store/`` instead of
deleted, the notification block kept ``telegram`` as its *default* channel
(which, with the handler gone, made the default silently broken), and the
router schema still advertised it. This test encodes the directive itself
so a partial removal can never look complete again.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCANNED_DIRS = ("app", "block_store")


def test_no_telegram_anywhere_in_source():
    offenders = []
    for base in SCANNED_DIRS:
        root = REPO_ROOT / base
        if not root.is_dir():
            continue
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "telegram" in text.lower():
                offenders.append(str(path.relative_to(REPO_ROOT)))
    assert not offenders, (
        "Telegram references found — the owner has asked repeatedly for "
        f"complete removal: {offenders}"
    )


def test_no_telegram_env_knob_documented():
    text = (REPO_ROOT / ".env.example").read_text(encoding="utf-8").lower()
    assert "telegram" not in text


def test_notification_send_requires_an_explicit_channel():
    """The old default channel was telegram; with the handler long gone the
    default was a guaranteed error. No silent default may replace it."""
    from app.routers.notification import SendRequest

    with pytest.raises(Exception):
        SendRequest(message="hi")  # no channel — must not silently pick one

    req = SendRequest(channel="email", message="hi")
    assert req.channel == "email"


@pytest.mark.asyncio
async def test_notification_block_rejects_telegram_channel():
    from app.blocks.notification import NotificationBlock

    block = NotificationBlock()
    result = await block._send({"channel": "telegram", "message": "hi"})
    assert result["status"] == "error"
    assert "telegram" in result["error"].lower() or "unknown" in result["error"].lower()
