"""Tests for container kit manifest parsing and CLI wiring."""

import json
from pathlib import Path

import pytest

from app.core.container_kit_store import _bundle_ready, _skeleton_ready


KITS_DIR = Path(__file__).resolve().parents[2] / "block_store" / "kits"


def _load_manifest(kit_id: str) -> dict:
    path = KITS_DIR / kit_id / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_construction_manifest_has_cli_metadata():
    manifest = _load_manifest("construction")
    assert "cli" in manifest
    assert manifest["cli"]["command"] == "cerebrum"
    assert manifest["cli"]["config_template"] == "cli/config.toml.example"


def test_construction_manifest_cli_artifacts_resolve():
    manifest = _load_manifest("construction")
    bundle_dir = KITS_DIR / "construction" / "bundle"
    cli_artifacts = [a for a in manifest.get("artifacts", []) if a["src"].startswith("cli/")]
    assert len(cli_artifacts) > 0
    for item in cli_artifacts:
        assert (bundle_dir / item["src"]).exists(), f"missing {item['src']}"
        assert item["dest"].startswith("cli/")


def test_construction_bundle_ready():
    manifest = _load_manifest("construction")
    assert _bundle_ready(KITS_DIR / "construction", manifest)


def test_template_manifest_has_cli_metadata():
    # _template/manifest.json is a Jinja2-style template, not strict JSON.
    text = (KITS_DIR / "_template" / "manifest.json").read_text(encoding="utf-8")
    assert '"cli"' in text
    assert '"command": "cerebrum"' in text
    assert '"config_template": "cli/config.toml.example"' in text


def test_template_manifest_cli_skeleton_artifacts_resolve():
    text = (KITS_DIR / "_template" / "manifest.json").read_text(encoding="utf-8")
    kit_dir = KITS_DIR / "_template"
    # Verify the CLI skeleton artifact src/dest entries exist as text and on disk.
    assert '"src": "cli/config.toml.example"' in text
    assert '"dest": "cli/config.toml.example"' in text
    assert (kit_dir / "cli" / "config.toml.example").exists()


def test_template_skeleton_ready():
    # Because _template/manifest.json is templated, parse it by stripping the
    # {{tags_json}} placeholder and replacing it with a valid JSON array.
    text = (KITS_DIR / "_template" / "manifest.json").read_text(encoding="utf-8")
    rendered = text.replace('"tags": {{tags_json}},', '"tags": [],')
    manifest = json.loads(rendered)
    assert _skeleton_ready(KITS_DIR / "_template", manifest)


@pytest.mark.parametrize(
    "kit_id",
    [
        "agriculture",
        "automotive",
        "aviation",
        "construction",
        "education",
        "finance",
        "hotel_management",
        "hr",
        "insurance",
        "legal",
        "manufacturing",
        "medical",
        "oil_gas",
        "pharma",
        "real_estate",
        "retail",
        "supply_chain",
    ],
)
def test_kit_manifest_exposes_formula_executor_v2(kit_id: str):
    manifest = _load_manifest(kit_id)
    assert "formula_executor_v2" in manifest.get("blocks", []), f"{kit_id} missing formula_executor_v2"


@pytest.mark.parametrize(
    "kit_id",
    [
        "agriculture",
        "automotive",
        "aviation",
        "construction",
        "education",
        "finance",
        "hotel_management",
        "hr",
        "insurance",
        "legal",
        "manufacturing",
        "medical",
        "oil_gas",
        "pharma",
        "real_estate",
        "retail",
        "supply_chain",
    ],
)
def test_kit_bundle_includes_formula_executor_v2(kit_id: str):
    bundle_file = KITS_DIR / kit_id / "bundle" / "app" / "blocks" / "formula_executor_v2.py"
    assert bundle_file.exists(), f"{kit_id} bundle missing formula_executor_v2.py"


def test_the_universal_kit_declares_a_universal_set():
    """No jurisdiction-specific figure may be encoded in the universal set.

    A tax or interest rate written here would be wrong for most businesses
    that load it, and would be a figure nobody can check. Rates are inputs;
    the one convention that does carry numbers says so.
    """
    manifest = _load_manifest("universal_business")
    assert manifest["status"] == "available"
    assert manifest.get("flow") == "independent", "composition must be declared"

    data = json.loads(
        (KITS_DIR / "universal_business" / "app" / "data" / "universal_formulas.json")
        .read_text(encoding="utf-8")
    )
    assert data["provenance"]["kind"] in ("internal_protocol", "regulator", "spc")
    assert data["provenance"]["reference"].strip()

    for formula in data["formulas"]:
        assert formula["expression"].strip(), formula["id"]
        assert formula["inputs"], formula["id"]
        # Every rate must arrive as a named input. A bare decimal literal in an
        # expression is an encoded rate wearing a formula's clothes.
        for token in formula["expression"].replace("(", " ").replace(")", " ").split():
            if token.replace(".", "", 1).isdigit():
                assert float(token) in (0.0, 1.0, 2.0), (
                    f"{formula['id']} encodes the literal {token!r}; "
                    "rates belong in inputs, not in the expression"
                )


def test_every_installable_kit_registers_its_blocks():
    """An installable kit with no block spec map installs and does nothing.

    ``kit_block_specs`` logs "no block spec map -- skipped" and registers zero
    blocks, so the kit is offered, installs cleanly, and is inert. Nothing
    else catches that: the composition audit passes it and ``_installable``
    passes it. This is the only gate that would notice.
    """
    from app.core.container_kit_store import list_kits
    from app.core.domain_kit_loader import _KIT_BLOCK_SPECS

    inert = [
        kit["id"]
        for kit in list_kits()
        if kit.get("installable") and kit["id"] not in _KIT_BLOCK_SPECS
    ]
    assert not inert, f"installable but registers no blocks: {inert}"
