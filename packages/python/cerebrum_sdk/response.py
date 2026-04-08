"""Response classes for Cerebrum SDK."""

from typing import Dict, Any, Optional


class ChatResponse:
    """Response from a chat completion.
    
    Attributes:
        text: The generated text response
        model: Model used for generation
        provider: AI provider (openai, anthropic, groq)
        tokens_used: Total tokens consumed
        finish_reason: Why generation stopped
    
    Example:
        >>> response = await client.chat("Hello!")
        >>> print(response.text)
        "Hello! How can I help you?"
        >>> print(f"Used {response.tokens_used} tokens")
    """
    
    def __init__(self, data: Dict[str, Any]):
        self._data = data
    
    @property
    def text(self) -> str:
        """The generated text response."""
        return self._data.get("text", "")
    
    @property
    def model(self) -> str:
        """Model used for generation."""
        return self._data.get("model", "")
    
    @property
    def provider(self) -> str:
        """AI provider used."""
        return self._data.get("provider", "")
    
    @property
    def tokens_used(self) -> int:
        """Total tokens consumed."""
        return self._data.get("tokens_total", 0)
    
    @property
    def finish_reason(self) -> str:
        """Why generation stopped."""
        return self._data.get("finish_reason", "")
    
    @property
    def raw(self) -> Dict[str, Any]:
        """Raw response data."""
        return self._data
    
    def __str__(self) -> str:
        return self.text
    
    def __repr__(self) -> str:
        text_preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"ChatResponse(text='{text_preview}', tokens={self.tokens_used})"


class StreamChunk:
    """A chunk from a streaming response.
    
    Attributes:
        text: Text content of this chunk
        done: Whether this is the final chunk
    
    Example:
        >>> async for chunk in client.chat.stream("Tell me a story"):
        ...     if not chunk.done:
        ...         print(chunk.text, end="")
    """
    
    def __init__(self, data: Dict[str, Any]):
        self._data = data
    
    @property
    def text(self) -> str:
        """Text content of this chunk."""
        return self._data.get("content", "")
    
    @property
    def done(self) -> bool:
        """Whether this is the final chunk."""
        return self._data.get("done", False)
    
    @property
    def raw(self) -> Dict[str, Any]:
        """Raw chunk data."""
        return self._data
    
    def __str__(self) -> str:
        return self.text
    
    def __repr__(self) -> str:
        return f"StreamChunk(text='{self.text[:30]}...', done={self.done})"
