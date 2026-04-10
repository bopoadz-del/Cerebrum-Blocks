"""All AI and Drive blocks."""

# AI Blocks
from .pdf import PDFBlock
from .ocr import OCRBlock
from .chat import ChatBlock
from .voice import VoiceBlock
from .vector_search import VectorSearchBlock
from .image import ImageBlock
from .translate import TranslateBlock
from .code import CodeBlock
from .web import WebBlock
from .search import SearchBlock
from .zvec import ZvecBlock

# Drive Blocks
from .google_drive import GoogleDriveBlock
from .onedrive import OneDriveBlock
from .local_drive import LocalDriveBlock
from .android_drive import AndroidDriveBlock

__all__ = [
    # AI Blocks
    "PDFBlock",
    "OCRBlock",
    "ChatBlock",
    "VoiceBlock",
    "VectorSearchBlock",
    "ImageBlock",
    "TranslateBlock",
    "CodeBlock",
    "WebBlock",
    "SearchBlock",
    "ZvecBlock",
    # Drive Blocks
    "GoogleDriveBlock",
    "OneDriveBlock",
    "LocalDriveBlock",
    "AndroidDriveBlock",
]

BLOCK_REGISTRY = {}

def register_block(name: str, block_class):
    """Register a block class."""
    BLOCK_REGISTRY[name] = block_class

def get_block(name: str):
    """Get a block class by name."""
    return BLOCK_REGISTRY.get(name)

def get_all_blocks():
    """Get all registered blocks."""
    return BLOCK_REGISTRY

# Register all blocks
register_block("pdf", PDFBlock)
register_block("ocr", OCRBlock)
register_block("chat", ChatBlock)
register_block("voice", VoiceBlock)
register_block("vector_search", VectorSearchBlock)
register_block("image", ImageBlock)
register_block("translate", TranslateBlock)
register_block("code", CodeBlock)
register_block("web", WebBlock)
register_block("search", SearchBlock)
register_block("zvec", ZvecBlock)
register_block("google_drive", GoogleDriveBlock)
register_block("onedrive", OneDriveBlock)
register_block("local_drive", LocalDriveBlock)
register_block("android_drive", AndroidDriveBlock)
