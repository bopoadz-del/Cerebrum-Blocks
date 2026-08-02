"""The learning store must land on durable storage, not /tmp.

Shape note: this asserts on where the path RESOLVES under a realistic
environment, not that a particular constant was changed. The original defect
was invisible precisely because the code looked deliberate -- a named env var
with a default. What made it a bug was that the default pointed at a directory
the container throws away on every deploy, so accumulated user corrections
silently reset roughly daily and the engine appeared never to converge.
"""

from __future__ import annotations

import importlib
import os


def _reload_with_env(monkeypatch, **env):
    for key in ("LEARNING_ENGINE_STORAGE", "DATA_DIR"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    module = importlib.import_module("app.blocks.learning_engine")
    return importlib.reload(module)


def _norm(path: str) -> str:
    return path.replace("\\", "/")


def test_default_lands_on_the_data_dir_not_tmp(monkeypatch):
    module = _reload_with_env(monkeypatch, DATA_DIR="/app/data")
    resolved = _norm(module._STORAGE_PATH)

    assert "/tmp" not in resolved, (
        "learning store is on ephemeral storage; every deploy discards "
        "accumulated user corrections"
    )
    assert resolved.startswith("/app/data"), resolved


def test_explicit_override_still_wins(monkeypatch):
    module = _reload_with_env(
        monkeypatch,
        DATA_DIR="/app/data",
        LEARNING_ENGINE_STORAGE="/somewhere/else/store.json",
    )
    assert _norm(module._STORAGE_PATH) == "/somewhere/else/store.json"


def test_follows_data_dir_wherever_it_points(monkeypatch, tmp_path):
    """Durability comes from DATA_DIR being a mount, so it must track it."""
    module = _reload_with_env(monkeypatch, DATA_DIR=str(tmp_path))
    assert _norm(module._STORAGE_PATH).startswith(_norm(str(tmp_path)))


def test_state_written_there_survives_a_reload(monkeypatch, tmp_path):
    """Round trip: what is written must still be readable by a fresh import."""
    module = _reload_with_env(monkeypatch, DATA_DIR=str(tmp_path))
    target = module._STORAGE_PATH
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as handle:
        handle.write('{"formulas": {"demo": {"executions": 42}}}')

    reloaded = _reload_with_env(monkeypatch, DATA_DIR=str(tmp_path))
    with open(reloaded._STORAGE_PATH, encoding="utf-8") as handle:
        assert "42" in handle.read()
