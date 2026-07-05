"""Root pytest configuration.

The ``cli/`` package and its copies under ``block_store/kits/`` contain pytest
modules that are designed to be executed from their own directory (they import
the ``cerebrum_cli`` package by relative path). Collecting them from the repo
root causes a package-name clash with the top-level ``tests/`` directory, so we
ignore all ``cli/tests`` directories during root collection. Run them with
``cd cli && python -m pytest tests/`` when needed.
"""

import os

# Match tests/conftest.py: extended blocks are registered in test sessions.
os.environ.setdefault("CEREBRUM_VIRGIN", "false")

collect_ignore_glob = [
    "cli/tests",
    "block_store/kits/_template/cli/tests",
    "block_store/kits/construction/bundle/cli/tests",
]
