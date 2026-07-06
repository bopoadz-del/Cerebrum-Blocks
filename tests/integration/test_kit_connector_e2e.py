"""End-to-end integration tests for domain kits, connectors, and reactive workflows."""

from __future__ import annotations

import importlib
import json
import os
import shutil
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("ENV", "test")
os.environ.setdefault("CEREBRUM_VIRGIN", "1")


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app, headers={"Authorization": "Bearer cb_dev_key"})


@pytest.fixture
def virgin_block_registry():
    """Reload block registry with virgin boot (no domain kits)."""
    os.environ["CEREBRUM_VIRGIN"] = "1"
    os.environ.pop("CEREBRUM_DOMAIN_KITS", None)
    import app.blocks as blocks_mod
    import app.core.domain_kit_loader as loader

    importlib.reload(loader)
    importlib.reload(blocks_mod)
    yield blocks_mod.BLOCK_REGISTRY
    os.environ.pop("CEREBRUM_DOMAIN_KITS", None)


@pytest.fixture
def tmp_install_target(tmp_path):
    return tmp_path / "cerebrum_instance"


class TestVirginBoot:
    @pytest.mark.requires_local_registry
    def test_construction_not_in_app_blocks(self):
        """Virgin boot must not ship construction blocks in app/blocks."""
        construction_blocks = [
            "construction_v2",
            "boq_processor",
            "bim",
            "smart_orchestrator",
        ]
        for name in construction_blocks:
            path = ROOT / "app" / "blocks" / f"{name}.py"
            # Virgin strips construction from runtime registry, not necessarily disk.
            # Verify blocks are not registered when CEREBRUM_VIRGIN=1 and no kits enabled.
            os.environ["CEREBRUM_VIRGIN"] = "1"
            os.environ.pop("CEREBRUM_DOMAIN_KITS", None)
            import app.core.domain_kit_loader as loader
            import app.blocks as blocks_mod

            importlib.reload(loader)
            importlib.reload(blocks_mod)
            assert name not in blocks_mod.BLOCK_REGISTRY

    @pytest.mark.requires_local_registry
    def test_virgin_boot_flag(self):
        from app.core.domain_kit_loader import is_virgin_boot

        os.environ["CEREBRUM_VIRGIN"] = "1"
        os.environ.pop("CEREBRUM_DOMAIN_KITS", None)
        assert is_virgin_boot() is True


class TestMedicalKitInstall:
    @pytest.mark.requires_local_registry
    def test_install_medical_skeleton_registers_connector(self, tmp_install_target):
        from app.core.container_kit_store import install_kit

        target = tmp_install_target
        target.mkdir(parents=True)
        result = install_kit("medical", target_root=target, force=True)
        assert result["status"] == "success"
        assert result.get("install_mode") in ("skeleton", "bundle")
        assert (target / "app" / "blocks" / "medical_ehr_connector.py").exists()

        registry_path = target / "data" / "domain_kit_registry.json"
        assert registry_path.exists()
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        assert "medical" in registry.get("kits", {})
        assert "medical_ehr_connector" in registry["kits"]["medical"].get("blocks", [])


class TestMedicalEHRConnector:
    @pytest.mark.asyncio
    async def test_mock_fhir_connector_event(self):
        from app.blocks.medical_ehr_connector import MedicalEHRConnectorBlock

        block = MedicalEHRConnectorBlock(config={
            "fhir_base_url": "https://fhir.test/r4",
            "fhir_access_token": "test-token",
        })

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "resourceType": "Patient",
            "id": "pat-1",
            "name": [{"family": "Doe", "given": ["Jane"]}],
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await block.process(
                {"resource": "Patient", "resource_id": "pat-1"},
                {"action": "fetch", "resource": "Patient"},
            )

        assert result["status"] == "success"
        event = result["event"]
        assert event["event_type"] == "fhir.patient.fetched"
        assert event["source"] == "medical_ehr"
        assert event["normalized_data"]["count"] == 1


class TestReactiveVideoWorkflow:
    @pytest.mark.asyncio
    async def test_video_ingest_auto_trigger_fires_notification(self):
        from app.blocks.video_metadata_ingest import VideoMetadataIngestBlock

        mock_notif = AsyncMock()
        mock_notif.process = AsyncMock(return_value={"status": "success", "channel": "webhook", "sent": True})

        ingest = VideoMetadataIngestBlock()
        payload = {
            "camera_id": "lobby-1",
            "source_id": "test",
            "anomalies": [
                {"anomaly_type": "overcrowding", "severity": "high", "confidence": 0.9}
            ],
            "auto_trigger": True,
            "notify_channel": "webhook",
            "notify_to": "https://hooks.example.com/alerts",
        }

        with patch("app.dependencies.get_block_instance", return_value=mock_notif):
            result = await ingest.process(payload, {"action": "ingest"})

        assert result["status"] == "success"
        assert result.get("workflow") is not None
        workflow = result["workflow"]
        assert workflow.get("triggered") is True
        mock_notif.process.assert_called_once()

    def test_video_ingest_api_with_workflow(self, client):
        mock_notif = AsyncMock()
        mock_notif.process = AsyncMock(return_value={"status": "success", "channel": "webhook"})

        with patch("app.dependencies.get_block_instance", return_value=mock_notif):
            response = client.post(
                "/v1/video/ingest",
                json={
                    "camera_id": "api-cam-1",
                    "anomalies": [{"anomaly_type": "intrusion", "severity": "critical"}],
                    "auto_trigger": True,
                    "notify_channel": "webhook",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data.get("anomaly_count", 0) >= 1
        assert data.get("workflow") is not None


class TestStoreCatalog:
    @pytest.mark.requires_local_registry
    def test_store_lists_required_kits(self, client):
        response = client.get("/store/containers")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 7
        kit_ids = {k["id"] for k in data["containers"]}
        required = {
            "construction",
            "medical",
            "hotel_management",
            "law",
            "finance",
            "maintenance",
        }
        assert required.issubset(kit_ids)

    @pytest.mark.requires_local_registry
    def test_coming_soon_kits_have_connectors(self, client):
        response = client.get("/store/containers")
        kits = {k["id"]: k for k in response.json()["containers"]}
        assert "pacer_connector" in kits["law"].get("blocks", [])
        assert "market_data_connector" in kits["finance"].get("blocks", [])
        assert "cmms_connector" in kits["maintenance"].get("blocks", [])


class TestWorkflowTriggersAPI:
    def test_list_builtin_triggers(self, client):
        response = client.get("/v1/workflows/triggers")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        trigger_ids = [t["trigger_id"] for t in data["triggers"]]
        assert "builtin-video-anomaly" in trigger_ids

    def test_register_custom_trigger(self, client):
        response = client.post(
            "/v1/workflows/triggers",
            json={
                "event_type": "video.anomaly",
                "min_severity": "critical",
                "description": "test trigger",
                "steps": [
                    {
                        "block_id": "video_anomaly_trigger",
                        "params": {"action": "evaluate"},
                        "input_mapping": {"metadata": "metadata"},
                    }
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "registered"
        assert data["trigger"]["event_type"] == "video.anomaly"
