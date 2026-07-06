"""Tests for the execute-router capability dispatch logic."""

from __future__ import annotations

import pytest

from app.routers.execute import should_run_out_of_process


def test_core_blocks_run_in_process():
    """Core blocks default to safe capabilities and run in-process."""
    assert not should_run_out_of_process("chat")
    assert not should_run_out_of_process("pdf")


def test_safe_registry_blocks_run_in_process():
    """Registry blocks with no elevated capabilities run in-process."""
    assert not should_run_out_of_process("construction_v2")


def test_block_with_network_runs_out_of_process(tmp_path, monkeypatch):
    """A registry block declaring network access runs out-of-process."""
    import json
    from app.core.block_capabilities import BlockCapabilities

    registry_root = tmp_path / "block_registry"
    block_dir = registry_root / "net_block"
    block_dir.mkdir(parents=True)
    (block_dir / "block.json").write_text(
        json.dumps({
            "id": "net_block",
            "permissions": {"network": True, "filesystem": False, "imports": [], "blocks": []},
        })
    )
    caps = BlockCapabilities.from_registry("net_block", registry_root)
    assert caps.has_network
    assert not caps.is_safe_for_in_process


def test_block_with_filesystem_runs_out_of_process(tmp_path):
    """A registry block declaring filesystem access runs out-of-process."""
    import json
    from app.core.block_capabilities import BlockCapabilities

    registry_root = tmp_path / "block_registry"
    block_dir = registry_root / "fs_block"
    block_dir.mkdir(parents=True)
    (block_dir / "block.json").write_text(
        json.dumps({
            "id": "fs_block",
            "permissions": {"network": False, "filesystem": ["/tmp"], "imports": [], "blocks": []},
        })
    )
    caps = BlockCapabilities.from_registry("fs_block", registry_root)
    assert caps.has_filesystem
    assert not caps.is_safe_for_in_process


def test_block_with_privileged_import_runs_out_of_process(tmp_path):
    """A registry block declaring a privileged import runs out-of-process."""
    import json
    from app.core.block_capabilities import BlockCapabilities

    registry_root = tmp_path / "block_registry"
    block_dir = registry_root / "os_block"
    block_dir.mkdir(parents=True)
    (block_dir / "block.json").write_text(
        json.dumps({
            "id": "os_block",
            "permissions": {"network": False, "filesystem": False, "imports": ["os"], "blocks": []},
        })
    )
    caps = BlockCapabilities.from_registry("os_block", registry_root)
    assert "os" in caps.privileged_imports
    assert not caps.is_safe_for_in_process
