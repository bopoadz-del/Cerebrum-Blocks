#!/usr/bin/env python3
"""Verify the publisher signature and file integrity of a block folder."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root so app imports work when run from scripts/.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.publisher_registry import BlockVerifier, PublisherRegistry


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a block folder's signature and digests."
    )
    parser.add_argument("--block", required=True, type=Path, help="Path to block folder")
    parser.add_argument(
        "--publisher",
        help="Expected publisher ID (optional; verifies manifest matches if provided)",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=None,
        help="Override path to publishers.json",
    )
    args = parser.parse_args()

    registry = PublisherRegistry(path=args.registry)
    verifier = BlockVerifier(registry=registry)
    result = verifier.verify_block(
        block_path=Path(args.block),
        publisher_id=args.publisher,
    )

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    sys.exit(main())
