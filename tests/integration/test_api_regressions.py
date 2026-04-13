"""Regression tests for recently hardened API behavior."""

import pytest
from fastapi.testclient import TestClient

from app.containers.security import SecurityContainer
from app.main import app


client = TestClient(app)


@pytest.mark.asyncio
async def test_dev_key_is_rejected_in_production(monkeypatch):
    """Development auth bypass must never work in production mode."""
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("CB_DEV_KEY", "dev-secret")

    container = SecurityContainer()
    result = await container.auth({"api_key": "dev-secret"})

    assert result["authenticated"] is False
    assert result["error"] == "Invalid key"


@pytest.mark.asyncio
async def test_dev_key_is_allowed_only_in_development(monkeypatch):
    """Development auth shortcut should stay available for local development."""
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("CB_DEV_KEY", "dev-secret")

    container = SecurityContainer()
    result = await container.auth({"api_key": "dev-secret"})

    assert result["authenticated"] is True
    assert result["key_id"] == "dev"
    assert result["role"] == "admin"


def test_v1_block_detail_route_uses_block_info_handler():
    """The v1 block detail route should resolve through the same handler as /blocks/{name}."""
    response = client.get("/v1/blocks/security")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "security"
    assert data["config"]["version"] == "1.0"