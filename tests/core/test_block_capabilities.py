"""Tests for the block capability model."""

from __future__ import annotations

import pytest

from app.core.block_capabilities import BlockCapabilities


def test_default_capabilities_are_safe():
    caps = BlockCapabilities()
    assert not caps.has_network
    assert not caps.has_filesystem
    assert caps.is_safe_for_in_process


def test_network_capability_is_unsafe():
    caps = BlockCapabilities(network=True)
    assert caps.has_network
    assert not caps.is_safe_for_in_process


def test_filesystem_capability_is_unsafe():
    caps = BlockCapabilities(filesystem=True)
    assert caps.has_filesystem
    assert not caps.is_safe_for_in_process


def test_filesystem_list_capability_is_unsafe():
    caps = BlockCapabilities(filesystem=["/tmp"])
    assert caps.has_filesystem
    assert not caps.is_safe_for_in_process


def test_privileged_imports():
    caps = BlockCapabilities(imports=["os", "math", "requests"])
    assert sorted(caps.privileged_imports) == ["os", "requests"]
    assert not caps.is_safe_for_in_process


def test_allowed_block_access():
    caps = BlockCapabilities(blocks=["memory", "config"])
    assert caps.allows_block_access("memory")
    assert not caps.allows_block_access("auth")
    assert not caps.is_safe_for_in_process


def test_from_manifest():
    manifest = {
        "permissions": {
            "network": False,
            "filesystem": ["/tmp"],
            "imports": ["os"],
            "blocks": ["memory"],
        }
    }
    caps = BlockCapabilities.from_manifest(manifest)
    assert caps.has_filesystem
    assert caps.blocks == ["memory"]
    assert "os" in caps.privileged_imports


def test_from_manifest_missing_permissions():
    caps = BlockCapabilities.from_manifest({})
    assert caps.is_safe_for_in_process


def test_from_registry_construction_v2():
    caps = BlockCapabilities.from_registry("construction_v2")
    assert caps.is_safe_for_in_process
