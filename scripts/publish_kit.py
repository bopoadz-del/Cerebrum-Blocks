#!/usr/bin/env python3
"""Publish a domain container kit to the Cerebrum Block Store.

Usage:
    python scripts/publish_kit.py --domain medical
    python scripts/publish_kit.py --domain medical --dry-run
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
KITS_DIR = PROJECT_ROOT / "block_store" / "kits"

# Human-readable titles for each kit.
_KIT_TITLES = {
    "construction": "Construction AEC Suite",
    "medical": "Medical & Healthcare Suite",
    "hotel_management": "Hotel Management & Hospitality Suite",
    "finance": "Finance & Investment Suite",
    "legal": "Legal & Contracts Suite",
    "retail": "Retail & E-commerce Suite",
    "pharma": "Pharmaceuticals & Life Sciences Suite",
    "insurance": "Insurance & Risk Suite",
    "supply_chain": "Supply Chain & Logistics Suite",
    "real_estate": "Real Estate & Property Suite",
    "automotive": "Automotive & Mobility Suite",
    "education": "Education & E-learning Suite",
    "agriculture": "Agriculture & AgriTech Suite",
    "hr": "Human Resources & Recruitment Suite",
    "manufacturing": "Manufacturing & Industry 4.0 Suite",
    "aviation": "Aviation & Aerospace Suite",
    "oil_gas": "Oil & Gas Suite",
}

# Domains that need a non-standard Pascal-case class name.
_CLASS_NAME_OVERRIDES = {
    "hr": "HR",
}

# Domains whose source filenames don't follow the default pattern.
_FILE_NAME_OVERRIDES = {
    "hotel_management": {
        "block": "hotel",
        "knowledge": "hotel",
        "types": "hotel",
    },
}


def _file_prefix(domain: str, component: str) -> str:
    return _FILE_NAME_OVERRIDES.get(domain, {}).get(component, domain)


def _pascal_name(domain: str) -> str:
    """Convert domain id to a PascalCase prefix (e.g. oil_gas -> OilGas, hr -> HR)."""
    if domain in _CLASS_NAME_OVERRIDES:
        return _CLASS_NAME_OVERRIDES[domain]
    return "".join(part.title() for part in domain.split("_"))


def _artifact(src: str) -> dict[str, str]:
    return {"src": src, "dest": src}


def _build_manifest(domain: str) -> dict[str, object]:
    pascal = _pascal_name(domain)
    container_class = f"app.containers.{domain}.{pascal}Container"
    block_name = f"{domain}_v2"
    block_class = f"{pascal}BlockV2"

    title = _KIT_TITLES.get(domain, f"{pascal} Suite")
    description = (
        f"{title}: typed document analysis, entity extraction, metrics, "
        f"compliance checks, and risk scoring for the {domain.replace('_', ' ')} domain."
    )

    # Source files that make up the full domain kit.
    block_prefix = _file_prefix(domain, "block")
    knowledge_prefix = _file_prefix(domain, "knowledge")
    types_prefix = _file_prefix(domain, "types")
    source_files = [
        f"app/containers/{domain}.py",
        f"app/blocks/{block_prefix}_v2.py",
        f"app/core/{knowledge_prefix}_knowledge.py",
        f"app/core/{types_prefix}_types.py",
    ]

    # Shared infrastructure required by all v2 domain blocks.
    shared_files = [
        "app/core/confidence.py",
        "app/core/schema_registry.py",
        "app/core/domain_block_v2.py",
        "app/core/metric_utils.py",
        "app/core/typed_block.py",
        "app/core/universal_base.py",
        "app/containers/base.py",
        "app/core/sandbox.py",
        "app/prompts/codegen_system.py",
        "app/blocks/formula_executor_v2.py",
    ]

    artifacts = [_artifact(path) for path in source_files + shared_files]

    return {
        "id": domain,
        "name": title,
        "version": "1.0.0",
        "description": description,
        "status": "available",
        "author": "bopoadz-del",
        "tags": ["domain", "container", domain],
        "source": {
            "repo": "https://github.com/bopoadz-del/Cerebrum-Blocks",
            "ref": "main",
            "publish_script": "scripts/publish_kit.py",
        },
        "container": {
            "class": container_class,
            "default_chat_prompt": None,
        },
        "blocks": [
            "pdf",
            "ocr",
            "chat",
            "image",
            block_name,
            "formula_executor_v2",
        ],
        "prompts": [],
        "data": [],
        "core_modules": [
            f"app/core/{knowledge_prefix}_knowledge.py",
            f"app/core/{types_prefix}_types.py",
            "app/core/confidence.py",
            "app/core/schema_registry.py",
            "app/core/domain_block_v2.py",
            "app/core/metric_utils.py",
            "app/core/typed_block.py",
            "app/core/universal_base.py",
            "app/containers/base.py",
            "app/core/sandbox.py",
            "app/prompts/codegen_system.py",
        ],
        "artifacts": artifacts,
        "price_cents": 0,
        "install_requires": {
            "min_platform_version": "2.0.0",
            "python": ">=3.10",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish a domain kit to the Block Store")
    parser.add_argument("--domain", required=True, help="Domain kit id (e.g. medical)")
    parser.add_argument("--dry-run", action="store_true", help="Print actions only")
    args = parser.parse_args()

    domain = args.domain.strip().lower()
    kit_dir = KITS_DIR / domain
    bundle_dir = kit_dir / "bundle"
    manifest_path = kit_dir / "manifest.json"

    manifest = _build_manifest(domain)
    artifacts = manifest["artifacts"]

    # Validate source files.
    missing: list[str] = []
    for item in artifacts:
        src_path = PROJECT_ROOT / item["src"]
        if not src_path.exists():
            missing.append(item["src"])
    if missing:
        print(f"Missing source files for '{domain}':", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"[dry-run] would create {kit_dir}")
        print(f"[dry-run] would write {manifest_path}")
        for item in artifacts:
            print(f"[dry-run] would copy {item['src']} -> {bundle_dir / item['src']}")
        return 0

    kit_dir.mkdir(parents=True, exist_ok=True)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    # Copy artifacts into bundle preserving relative paths.
    copied = 0
    for item in artifacts:
        src = PROJECT_ROOT / item["src"]
        dest = bundle_dir / item["src"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        copied += 1

    # Write manifest.
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    print(f"Published '{domain}' kit: {copied} artifacts -> {bundle_dir}")
    print(f"Manifest written: {manifest_path}")

    # Publish gate. CI catches a bad manifest on the next push; this catches
    # it before the kit is on the shelf, which is the point at which a
    # consumer could install it. Reported, not silently swallowed -- and it
    # runs after the write so the findings name the manifest as published.
    from audit_kit_composition import (
        MODULES_DIR,
        REGISTRY_DIR,
        _dirs,
        _modules,
        audit_kit,
        load_known,
    )

    known = _dirs(REGISTRY_DIR) | _modules(MODULES_DIR)
    # Same registration contract as CI: a gap that is declared in
    # KNOWN_KIT_GAPS.md does not block, or publishing any already-registered
    # kit would fail while CI passes -- two gates disagreeing about the same
    # manifest is worse than either one alone.
    registered = load_known()
    findings = [
        (code, detail)
        for code, detail in audit_kit(domain, str(kit_dir.parent), known)
        if f"{domain} :: {code}" not in registered
    ]
    if findings:
        print(f"\nCOMPOSITION FINDINGS for '{domain}':")
        for code, detail in findings:
            print(f"  {code}: {detail}")
        print(
            "Kit is on the shelf but does not pass the composition audit. "
            f"Fix it, or register it in KNOWN_KIT_GAPS.md as '{domain} :: <code>'."
        )
        return 1
    print("Composition audit: clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
