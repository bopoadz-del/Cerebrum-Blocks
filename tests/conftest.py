"""Pytest configuration and fixtures."""

import pytest
import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Activate dev mode for the test session so cb_dev_key is loaded.
# The auth module no longer auto-detects pytest via sys.modules (that
# was a security hole — see app/core/auth.py:_is_dev_environment).
# Tests that need an authenticated client must declare themselves
# tests via this env var.
os.environ.setdefault("ENV", "test")

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
