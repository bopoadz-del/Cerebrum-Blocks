"""Document Engine block for Cerebrum-Blocks.

Provides Parse → Reason → Map pipeline for technical document intelligence.
"""
import importlib.util
import os
from .main import main, parse_all
from .reasoner import DocumentReasoner, ReasonedOutput
from .mapper import DocumentMapper, StructuredDocument

# The block wrapper lives in app/blocks/document_engine.py, but the package
# directory shadows the module file for ``import app.blocks.document_engine``.
# Load the wrapper explicitly and re-export it so both import paths work.
_BLOCK_MODULE_NAME = "app.blocks.document_engine_block"
_BLOCK_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "document_engine.py")
_spec = importlib.util.spec_from_file_location(_BLOCK_MODULE_NAME, _BLOCK_FILE_PATH)
_block_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_block_module)
DocumentEngineBlock = _block_module.DocumentEngineBlock

__all__ = [
    "main",
    "parse_all",
    "DocumentReasoner",
    "ReasonedOutput",
    "DocumentMapper",
    "StructuredDocument",
    "DocumentEngineBlock",
]
