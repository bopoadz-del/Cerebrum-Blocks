"""Cerebrum SDK - Build AI Like Lego.

Official Python SDK for Cerebrum Blocks API.

Example:
    >>> from cerebrum_sdk import Cerebrum
    >>> client = Cerebrum(api_key="cb_your_key_here")
    >>> response = await client.chat("Hello!")
    >>> print(response.text)
    
    Streaming:
    >>> async for chunk in client.chat.stream("Tell me a story"):
    ...     print(chunk.text, end="")
"""

__version__ = "1.0.0"
__author__ = "Cerebrum Team"

from .client import Cerebrum, CerebrumClient
from .chain import Chain, chain
from .response import ChatResponse, StreamChunk
from .exceptions import (
    CerebrumError,
    AuthenticationError,
    RateLimitError,
    BlockNotFoundError,
    ExecutionError,
)

__all__ = [
    "Cerebrum",
    "CerebrumClient",
    "Chain",
    "chain",
    "ChatResponse",
    "StreamChunk",
    "CerebrumError",
    "AuthenticationError",
    "RateLimitError",
    "BlockNotFoundError",
    "ExecutionError",
]
