"""Cerebrum Blocks Python SDK.

Build AI like Lego. One API. 13 blocks.

Quickstart:
    from cerebrum import CerebrumClient
    
    client = CerebrumClient(api_key="your-key")
    response = client.chat("Hello!")
    print(response.text)
"""

from .client import CerebrumClient
from .chain import chain, ChainResult
from .streaming import StreamResponse

__version__ = "1.0.0"
__all__ = ["CerebrumClient", "chain", "ChainResult", "StreamResponse"]
