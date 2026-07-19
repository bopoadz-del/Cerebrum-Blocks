"""Tests for BaseConnector registry integration."""

import pytest

from app.blocks.core.base_connector import BaseConnector
from app.core.connector_events import ConnectorEvent


class DummyConnector(BaseConnector):
    name = "dummy_connector"
    connector_source = "dummy"
    version = "1.0.0"
    description = "Dummy connector for tests"
    default_config = {"api_key": ""}

    async def fetch_raw(self, input_data, params):
        return {"data": "ok"}


@pytest.mark.asyncio
async def test_to_registry_entry():
    connector = DummyConnector()
    entry = connector.to_registry_entry()
    assert entry["connector_id"] == "dummy"
    assert entry["block"] == "dummy_connector"
    assert "api_key" in entry["schema"]
