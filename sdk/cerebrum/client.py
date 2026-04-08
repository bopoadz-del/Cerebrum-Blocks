"""Cerebrum Blocks Python SDK client."""

import os
from typing import Any, Dict, List, Optional, Iterator
import httpx


class CerebrumClient:
    """Client for the Cerebrum Blocks API.
    
    Args:
        api_key: Your Cerebrum API key. Defaults to CEREBRUM_API_KEY env var.
        base_url: API endpoint. Defaults to https://api.cerebrumblocks.com
    
    Example:
        >>> from cerebrum import CerebrumClient
        >>> client = CerebrumClient(api_key="sk-...")
        >>> response = client.chat("Explain quantum computing")
        >>> print(response.text)
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("CEREBRUM_API_KEY")
        self.base_url = (base_url or os.getenv("CEREBRUM_BASE_URL", "https://api.cerebrumblocks.com")).rstrip("/")
        self._client = httpx.Client(timeout=60.0)
    
    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def _post(self, endpoint: str, json: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request."""
        url = f"{self.base_url}{endpoint}"
        response = self._client.post(url, headers=self._headers(), json=json)
        response.raise_for_status()
        return response.json()
    
    def _get(self, endpoint: str) -> Dict[str, Any]:
        """Make a GET request."""
        url = f"{self.base_url}{endpoint}"
        response = self._client.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    # -------------------- CHAT --------------------
    
    def chat(self, message: str, **kwargs) -> "ChatResponse":
        """Send a chat message.
        
        Args:
            message: The message to send
            model: Model to use (e.g., "gpt-3.5-turbo", "claude-3-haiku")
            system: System prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            provider: "openai", "anthropic", or "mock"
        
        Returns:
            ChatResponse object with .text, .tokens_used, etc.
        """
        payload = {
            "message": message,
            "model": kwargs.get("model", "gpt-3.5-turbo"),
            "system": kwargs.get("system", "You are a helpful assistant."),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.7),
            "provider": kwargs.get("provider", "openai"),
        }
        result = self._post("/v1/chat", payload)
        return ChatResponse(result)
    
    def chat_stream(self, message: str, **kwargs) -> Iterator["StreamChunk"]:
        """Stream a chat response.
        
        Yields:
            StreamChunk objects with .text and .done
        """
        import json
        
        payload = {
            "message": message,
            "model": kwargs.get("model", "gpt-3.5-turbo"),
            "system": kwargs.get("system", "You are a helpful assistant."),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.7),
            "provider": kwargs.get("provider", "openai"),
            "stream": True,
        }
        
        url = f"{self.base_url}/v1/chat/stream"
        with httpx.stream("POST", url, headers=self._headers(), json=payload, timeout=60.0) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        yield StreamChunk(chunk)
                    except json.JSONDecodeError:
                        continue
    
    # -------------------- VECTOR SEARCH --------------------
    
    def vector_add(self, documents: List[Dict[str, Any]], collection: str = "default") -> Dict[str, Any]:
        """Add documents to vector search.
        
        Args:
            documents: List of {"text": str, "metadata": dict} objects
            collection: Collection name
        """
        return self._post("/v1/vector/add", {
            "documents": documents,
            "collection": collection
        })
    
    def vector_query(self, query: str, collection: str = "default", top_k: int = 5) -> List[Dict[str, Any]]:
        """Query vector search.
        
        Args:
            query: Search query
            collection: Collection name
            top_k: Number of results
        
        Returns:
            List of matching documents with scores
        """
        result = self._post("/v1/vector/search", {
            "query": query,
            "collection": collection,
            "top_k": top_k
        })
        return result.get("results", [])
    
    # -------------------- BLOCKS --------------------
    
    def list_blocks(self) -> List[Dict[str, Any]]:
        """List all available blocks."""
        result = self._get("/v1/blocks")
        return result.get("blocks", [])
    
    def health(self) -> Dict[str, Any]:
        """Check API health."""
        return self._get("/v1/health")


class ChatResponse:
    """Response from a chat completion."""
    
    def __init__(self, data: Dict[str, Any]):
        self._data = data
    
    @property
    def text(self) -> str:
        """The generated text."""
        return self._data.get("text", "")
    
    @property
    def tokens_used(self) -> int:
        """Total tokens used."""
        return self._data.get("tokens_total", 0)
    
    @property
    def model(self) -> str:
        """Model used."""
        return self._data.get("model", "")
    
    @property
    def provider(self) -> str:
        """Provider used."""
        return self._data.get("provider", "")
    
    @property
    def raw(self) -> Dict[str, Any]:
        """Raw response data."""
        return self._data
    
    def __str__(self) -> str:
        return self.text
    
    def __repr__(self) -> str:
        return f"ChatResponse(text={self.text[:50]}..., model={self.model})"


class StreamChunk:
    """A single chunk from a streaming response."""
    
    def __init__(self, data: Dict[str, Any]):
        self._data = data
    
    @property
    def text(self) -> str:
        """Text content of this chunk."""
        return self._data.get("text", "")
    
    @property
    def done(self) -> bool:
        """Whether this is the final chunk."""
        return self._data.get("done", False)
    
    def __str__(self) -> str:
        return self.text
