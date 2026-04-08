"""Streaming utilities for Cerebrum SDK."""

from typing import Any, Dict


class StreamResponse:
    """Wrapper for streaming responses."""
    
    def __init__(self, iterator):
        self._iterator = iterator
        self._full_text = ""
    
    def __iter__(self):
        return self
    
    def __next__(self):
        chunk = next(self._iterator)
        self._full_text += chunk.text
        return chunk
    
    @property
    def full_text(self) -> str:
        """Get the full accumulated text."""
        # Drain the iterator if not already consumed
        try:
            while True:
                chunk = next(self._iterator)
                self._full_text += chunk.text
        except StopIteration:
            pass
        return self._full_text
