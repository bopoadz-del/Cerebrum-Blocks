"""Tests for StorageBlock upload security and archive features."""

import os

import pytest

from app.blocks.storage import StorageBlock


@pytest.fixture
def storage(tmp_path):
    return StorageBlock(config={"backend": "local", "data_dir": str(tmp_path)})


@pytest.mark.asyncio
async def test_upload_valid_file(storage):
    result = await storage.process({
        "action": "upload",
        "filename": "report.pdf",
        "content": b"PDF content",
        "allowed_extensions": [".pdf", ".csv"],
    })
    assert result["status"] == "success"
    assert result["filename"] == "report.pdf"


@pytest.mark.asyncio
async def test_upload_rejects_disallowed_extension(storage):
    result = await storage.process({
        "action": "upload",
        "filename": "malware.exe",
        "content": b"bad",
        "allowed_extensions": [".pdf", ".csv"],
    })
    assert result["status"] == "error"
    assert "extension" in result["error"].lower()


@pytest.mark.asyncio
async def test_upload_rejects_path_traversal(storage):
    result = await storage.process({
        "action": "upload",
        "filename": "../../../etc/passwd.txt",
        "content": b"bad",
        "allowed_extensions": [".txt"],
    })
    assert result["status"] == "error"
    assert "path" in result["error"].lower()


@pytest.mark.asyncio
async def test_upload_sanitizes_filename(storage, tmp_path):
    result = await storage.process({
        "action": "upload",
        "filename": "subfolder/report.pdf",
        "content": b"PDF content",
        "allowed_extensions": [".pdf"],
    })
    assert result["status"] == "success"
    assert result["filename"] == "report.pdf"
    assert result["stored_path"].startswith(str(tmp_path))
