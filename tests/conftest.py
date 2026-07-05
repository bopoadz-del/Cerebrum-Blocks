"""Pytest configuration and fixtures."""

import pytest
import os
import sys
from pathlib import Path

# Add app to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Activate dev mode for the test session so cb_dev_key is loaded.
# The auth module no longer auto-detects pytest via sys.modules (that
# was a security hole — see app/core/auth.py:_is_dev_environment).
# Tests that need an authenticated client must declare themselves
# tests via this env var.
os.environ.setdefault("ENV", "test")

# Extended blocks are only registered when the platform boots in legacy mode.
os.environ.setdefault("CEREBRUM_VIRGIN", "false")

CONSTRUCTION_CONTAINER_PATH = ROOT / "app" / "containers" / "construction.py"
CONSTRUCTION_V2_PATH = ROOT / "app" / "blocks" / "construction_v2.py"

requires_construction_kit = pytest.mark.skipif(
    not CONSTRUCTION_CONTAINER_PATH.exists(),
    reason=(
        "Construction kit not installed — run POST /store/containers/construction/install "
        "or copy from block_store/kits/construction/bundle/"
    ),
)

requires_construction_v2 = pytest.mark.skipif(
    not CONSTRUCTION_V2_PATH.exists(),
    reason=(
        "construction_v2 not installed — install construction kit from block_store "
        "or set CEREBRUM_DOMAIN_KITS=construction after install"
    ),
)

@pytest.fixture
def sample_text():
    return "Hello, this is a test document for Cerebrum Blocks."

@pytest.fixture
def sample_code():
    return """
def hello_world():
    print("Hello, World!")
    return 42

class MyClass:
    def __init__(self):
        self.value = 10
"""

@pytest.fixture
def data_dir():
    return "/app/data"
