#!/usr/bin/env python3
"""Publish the construction container kit from The Fork into Cerebrum Block Store.

Usage:
    python scripts/publish_construction_kit.py
    python scripts/publish_construction_kit.py --fork-root C:\\Users\\shimm\\The_Fork

Copies Fork-authored artifacts into block_store/kits/construction/bundle/
so GET /store/containers lists bundle_ready=true and install can run.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FORK = Path.home() / "The_Fork"
KIT_ID = "construction"
MANIFEST_PATH = PROJECT_ROOT / "block_store" / "kits" / KIT_ID / "manifest.json"
BUNDLE_DIR = PROJECT_ROOT / "block_store" / "kits" / KIT_ID / "bundle"


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish construction kit from The Fork")
    parser.add_argument(
        "--fork-root",
        type=Path,
        default=DEFAULT_FORK,
        help=f"Path to The Fork clone (default: {DEFAULT_FORK})",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print actions only")
    args = parser.parse_args()

    fork_root: Path = args.fork_root.resolve()
    if not fork_root.is_dir():
        print(f"Fork root not found: {fork_root}", file=sys.stderr)
        return 1
    if not MANIFEST_PATH.exists():
        print(f"Kit manifest missing: {MANIFEST_PATH}", file=sys.stderr)
        return 1

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts") or []
    if not artifacts:
        print("No artifacts listed in manifest.json", file=sys.stderr)
        return 1

    copied = 0
    missing = []

    for item in artifacts:
        rel_src = item["src"]
        fork_src = fork_root / rel_src
        bundle_dest = BUNDLE_DIR / rel_src

        if not fork_src.exists():
            missing.append(rel_src)
            continue

        if args.dry_run:
            print(f"would copy {fork_src} -> {bundle_dest}")
            copied += 1
            continue

        bundle_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fork_src, bundle_dest)
        print(f"copied {rel_src}")
        copied += 1

    if missing:
        print("\nMissing in Fork:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)

    print(f"\n{'Would copy' if args.dry_run else 'Copied'} {copied}/{len(artifacts)} artifacts")
    if missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
