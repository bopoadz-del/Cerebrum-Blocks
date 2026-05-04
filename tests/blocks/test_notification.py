"""Tests for Notification Block."""

import pytest
from app.blocks import NotificationBlock


@pytest.fixture
def notification_block():
    return NotificationBlock()


@pytest.mark.asyncio
async def test_notification_block_execute_structure(notification_block):
    result = await notification_block.execute(
        {"channel": "webhook", "url": "https://httpbin.org/post", "message": "test"},
        {"action": "send"},
    )
    assert "block" in result
    assert result["block"] == "notification"
    assert "request_id" in result
    assert "status" in result
    assert "result" in result


@pytest.mark.asyncio
async def test_notification_block_metadata(notification_block):
    assert notification_block.name == "notification"
    assert notification_block.config.version == "1.0.0"
    assert notification_block.config.requires_api_key == False


@pytest.mark.asyncio
async def test_notification_health(notification_block):
    result = await notification_block.execute(None, {"action": "health"})
    inner = result.get("result", result)
    assert inner.get("status") == "healthy"
    assert "available_channels" in inner


@pytest.mark.asyncio
async def test_notification_unknown_channel(notification_block):
    result = await notification_block.execute(
        {"channel": "sms", "to": "123", "message": "hi"},
        {"action": "send"},
    )
    inner = result.get("result", result)
    assert inner.get("status") == "error"


@pytest.mark.asyncio
async def test_notification_mcp_missing_block(notification_block):
    result = await notification_block.execute(
        {"channel": "mcp", "message": "hi"},
        {"action": "send"},
    )
    inner = result.get("result", result)
    assert inner.get("status") == "error"
    assert "block or tool name required" in inner.get("error", "")


@pytest.mark.asyncio
async def test_notification_webhook_missing_url(notification_block):
    result = await notification_block.execute(
        {"channel": "webhook", "message": "hi"},
        {"action": "send"},
    )
    inner = result.get("result", result)
    assert inner.get("status") == "error"


@pytest.mark.asyncio
async def test_notification_broadcast(notification_block):
    result = await notification_block.execute(
        {"channels": ["webhook", "webhook"], "url": "https://httpbin.org/post", "message": "test"},
        {"action": "broadcast"},
    )
    inner = result.get("result", result)
    assert inner.get("status") in ("success", "partial")
    assert "results" in inner
