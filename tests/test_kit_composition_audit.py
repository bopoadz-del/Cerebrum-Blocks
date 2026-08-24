"""The composition audit must actually refuse things.

A gate is only a gate if it blocks. These tests assert each finding fires on
a kit built to trigger it, that a well-formed kit is accepted, and that the
real repository passes -- so the audit cannot rot into a no-op that reports
success because it stopped looking.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "audit_kit_composition.py"


def _load():
    spec = importlib.util.spec_from_file_location("audit_kit_composition", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


audit = _load()


def _kit(root: Path, name: str, manifest, *, raw: str | None = None) -> Path:
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    text = raw if raw is not None else json.dumps(manifest)
    (d / "manifest.json").write_text(text, encoding="utf-8")
    return d


def _base(**over):
    body = {
        "id": "demo",
        "name": "Demo",
        "version": "1.0.0",
        "description": "d",
        "status": "available",
        "blocks": ["alpha", "beta"],
    }
    body.update(over)
    return body


def _codes(kit_dir: Path, kit: str, known=("alpha", "beta")):
    return [c for c, _ in audit.audit_kit(kit, str(kit_dir), set(known))]


# --------------------------------------------------------------------------
# Silence is not permission.
# --------------------------------------------------------------------------


def test_multi_block_kit_without_composition_is_a_finding(tmp_path):
    _kit(tmp_path, "demo", _base())
    assert "no_composition" in _codes(tmp_path, "demo")


def test_single_block_kit_needs_no_composition(tmp_path):
    _kit(tmp_path, "demo", _base(blocks=["alpha"]))
    assert "no_composition" not in _codes(tmp_path, "demo")


def test_flow_satisfies_the_composition_requirement(tmp_path):
    _kit(tmp_path, "demo", _base(flow=[["alpha"], ["beta"]]))
    assert _codes(tmp_path, "demo") == []


def test_waves_is_accepted_as_a_legacy_spelling(tmp_path):
    """universal_kernel predates this audit; migrating it would create two
    keys meaning the same thing."""
    _kit(tmp_path, "demo", _base(waves={"wave1": ["alpha"], "wave2": ["beta"]}))
    assert _codes(tmp_path, "demo") == []


def test_a_flat_flow_list_is_accepted(tmp_path):
    _kit(tmp_path, "demo", _base(flow=["alpha", "beta"]))
    assert _codes(tmp_path, "demo") == []


def test_an_empty_flow_does_not_pass_as_a_declaration(tmp_path):
    """Declaring `flow: []` for a two-block kit still leaves both unordered."""
    _kit(tmp_path, "demo", _base(flow=[]))
    assert "composition_incomplete" in _codes(tmp_path, "demo")


# --------------------------------------------------------------------------
# Agreement between the composition and the block list.
# --------------------------------------------------------------------------


def test_flow_omitting_a_block_is_a_finding(tmp_path):
    _kit(tmp_path, "demo", _base(flow=[["alpha"]]))
    codes = _codes(tmp_path, "demo")
    assert "composition_incomplete" in codes


def test_flow_ordering_a_non_member_is_a_finding(tmp_path):
    _kit(tmp_path, "demo", _base(flow=[["alpha", "beta", "ghost"]]))
    assert "composition_unknown_block" in _codes(tmp_path, "demo")


# --------------------------------------------------------------------------
# Manifest integrity.
# --------------------------------------------------------------------------


def test_unresolved_block_is_a_finding(tmp_path):
    _kit(tmp_path, "demo", _base(blocks=["alpha", "nope"], flow=["alpha", "nope"]))
    assert "unresolved_block" in _codes(tmp_path, "demo")


def test_a_kit_may_vendor_its_own_blocks(tmp_path):
    """universal_kernel resolves via wave1/... rather than block_registry."""
    d = _kit(tmp_path, "demo", _base(blocks=["local_one"], flow=["local_one"]))
    (d / "wave1" / "local_one").mkdir(parents=True)
    assert _codes(tmp_path, "demo", known=()) == []


def test_duplicate_blocks_are_a_finding(tmp_path):
    _kit(tmp_path, "demo", _base(blocks=["alpha", "alpha"], flow=["alpha"]))
    assert "duplicate_blocks" in _codes(tmp_path, "demo")


def test_id_mismatch_is_a_finding(tmp_path):
    _kit(tmp_path, "demo", _base(id="something_else", flow=["alpha", "beta"]))
    assert "id_mismatch" in _codes(tmp_path, "demo")


def test_missing_required_key_is_a_finding(tmp_path):
    body = _base(flow=["alpha", "beta"])
    del body["version"]
    _kit(tmp_path, "demo", body)
    assert "missing_key" in _codes(tmp_path, "demo")


def test_unparseable_manifest_is_a_finding_not_a_crash(tmp_path):
    _kit(tmp_path, "demo", None, raw="{not json")
    assert _codes(tmp_path, "demo") == ["manifest_unparseable"]


def test_missing_manifest_is_a_finding(tmp_path):
    (tmp_path / "demo").mkdir()
    assert _codes(tmp_path, "demo") == ["no_manifest"]


def test_blocks_must_be_a_list(tmp_path):
    _kit(tmp_path, "demo", _base(blocks="alpha"))
    assert "blocks_not_a_list" in _codes(tmp_path, "demo")


# --------------------------------------------------------------------------
# The audit as a CI gate.
# --------------------------------------------------------------------------


def test_registration_file_parses_known_gaps(tmp_path, monkeypatch):
    (tmp_path / "KNOWN_KIT_GAPS.md").write_text(
        "# heading\n\ntext\n\n- demo :: no_composition  because\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    assert audit.load_known() == {"demo :: no_composition"}


def _mini_repo(tmp_path: Path) -> Path:
    """A repo where alpha/beta resolve, so only the composition gap fires."""
    kits = tmp_path / "block_store" / "kits"
    _kit(kits, "demo", _base())
    for b in ("alpha", "beta"):
        (tmp_path / "block_registry" / b).mkdir(parents=True, exist_ok=True)
    return kits


def test_main_exits_nonzero_on_an_unregistered_finding(tmp_path, monkeypatch):
    _mini_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert audit.main([]) == 1


def test_main_exits_zero_once_the_finding_is_registered(tmp_path, monkeypatch):
    _mini_repo(tmp_path)
    (tmp_path / "KNOWN_KIT_GAPS.md").write_text(
        "- demo :: no_composition  registered\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    assert audit.main([]) == 0


def test_registration_does_not_suppress_a_different_finding(tmp_path, monkeypatch):
    """Registering one code must not blanket-silence the kit."""
    kits = _mini_repo(tmp_path)
    _kit(kits, "demo", _base(blocks=["alpha", "ghost"]))
    (tmp_path / "KNOWN_KIT_GAPS.md").write_text(
        "- demo :: no_composition  registered\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    assert audit.main([]) == 1


def test_the_template_kit_is_skipped_by_name_not_by_parse_failure(tmp_path, monkeypatch):
    """_template carries {{placeholders}} and cannot be JSON. Skipping it by
    name means a real kit with a broken manifest is still caught."""
    kits = tmp_path / "block_store" / "kits"
    _kit(kits, "_template", None, raw='{"id": "{{domain}}", "tags": {{tags_json}}}')
    _kit(kits, "real", None, raw="{also broken")
    monkeypatch.chdir(tmp_path)
    assert audit.main([]) == 1


# --------------------------------------------------------------------------
# Regression lock on the real repository.
# --------------------------------------------------------------------------


def test_this_repository_passes_the_audit(monkeypatch):
    monkeypatch.chdir(REPO)
    assert audit.main([]) == 0, "run: python scripts/audit_kit_composition.py"


def test_universal_kernel_declares_a_complete_composition(monkeypatch):
    """The worked example. If this regresses, the audit lost its only kit
    that demonstrates what a complete declaration looks like."""
    monkeypatch.chdir(REPO)
    known = audit._dirs(audit.REGISTRY_DIR) | audit._modules(audit.MODULES_DIR)
    assert audit.audit_kit("universal_kernel", audit.KITS_DIR, known) == []
