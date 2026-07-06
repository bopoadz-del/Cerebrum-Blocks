"""Tests for Local Drive Block.

The block was hardened in commit 61de979e:
  - read and write operations were removed (RCE / arbitrary FS access vector)
  - list paths must resolve inside DATA_DIR

These tests verify the post-hardening surface.
"""

import pytest
import os

from app.blocks import LocalDriveBlock


@pytest.fixture
def local_drive_block(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    return LocalDriveBlock()


@pytest.mark.asyncio
async def test_local_drive_block_execute_structure(local_drive_block):
    """Block returns the standardised UniversalBlock envelope."""
    result = await local_drive_block.execute(None, {"operation": "list"})
    for k in ("block", "request_id", "status", "result", "confidence",
              "metadata", "source_id", "processing_time_ms"):
        assert k in result
    assert result["block"] == "local_drive"


@pytest.mark.asyncio
async def test_local_drive_block_metadata(local_drive_block):
    """Block class metadata reflects the v2.0 sandboxed surface."""
    assert local_drive_block.name == "local_drive"
    # version bumped to 2.0 when read/write were removed
    assert local_drive_block.version == "1.1"


@pytest.mark.asyncio
async def test_local_drive_block_list(tmp_path, local_drive_block):
    """list operation returns files inside DATA_DIR."""
    (tmp_path / "a.txt").write_text("hi")
    (tmp_path / "subdir").mkdir()
    result = await local_drive_block.execute(None, {"operation": "list", "folder_path": "."})
    assert result["block"] == "local_drive"
    assert result["result"]["operation"] == "list"
    assert "files" in result["result"]
    names = {f["name"] for f in result["result"]["files"]}
    assert {"a.txt", "subdir"}.issubset(names)


@pytest.mark.asyncio
async def test_local_drive_write_is_sandboxed(local_drive_block, tmp_path):
    """Write is supported but confined to the drive root."""
    result = await local_drive_block.execute(
        None,
        {"operation": "write", "file_path": "x.txt", "content": "hello"},
    )
    assert result["result"]["status"] == "success"
    assert (tmp_path / "x.txt").read_text() == "hello"


@pytest.mark.asyncio
async def test_local_drive_rejects_path_outside_data_dir(local_drive_block):
    """Listing a path outside DATA_DIR is rejected."""
    result = await local_drive_block.execute(None, {"operation": "list", "folder_path": "../etc"})
    assert result["result"]["status"] == "error"
    err = result["result"].get("error", "")
    assert "escapes" in err.lower() or "outside" in err.lower() or "permitted" in err.lower()
