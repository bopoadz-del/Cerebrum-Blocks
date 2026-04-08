"""Cerebrum API Client."""

import os
import json
from typing import Optional, Dict, Any, List, AsyncGenerator, Union
from urllib.parse import urljoin

import httpx

from .response import ChatResponse, StreamChunk
from .exceptions import (
    CerebrumError,
    AuthenticationError,
    RateLimitError,
    BlockNotFoundError,
    ExecutionError,
)


class Cerebrum:
    """Official Cerebrum API Client.
    
    Build AI applications with modular blocks. One API key, 16 blocks,
    infinite possibilities.
    
    Args:
        api_key: Your Cerebrum API key (starts with 'cb_')
        base_url: API endpoint URL (default: https://api.cerebrumblocks.com)
        timeout: Request timeout in seconds (default: 60)
    
    Example:
        >>> from cerebrum_sdk import Cerebrum
        >>> 
        >>> # Initialize with API key
        >>> client = Cerebrum(api_key="cb_your_key_here")
        >>> 
        >>> # Simple chat
        >>> response = await client.chat("Explain quantum computing")
        >>> print(response.text)
        >>> 
        >>> # Streaming chat
        >>> async for chunk in client.chat.stream("Tell me a story"):
        ...     print(chunk.text, end="", flush=True)
    """
    
    DEFAULT_BASE_URL = "https://api.cerebrumblocks.com"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0
    ):
        self.api_key = api_key or os.getenv("CEREBRUM_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key required. Get one at https://cerebrumblocks.com/dashboard\n"
                "Set CEREBRUM_API_KEY environment variable or pass api_key="
            )
        
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": f"cerebrum-sdk-python/1.0.0",
                },
                timeout=self.timeout,
            )
        return self._client
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request and handle errors."""
        client = self._get_client()
        url = f"/v1{endpoint}"
        
        try:
            response = await client.request(method, url, **kwargs)
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded. Upgrade your plan.")
            elif response.status_code == 404:
                raise BlockNotFoundError(f"Endpoint not found: {endpoint}")
            elif response.status_code >= 500:
                raise ExecutionError(f"Server error: {response.text}")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise CerebrumError(f"HTTP {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise CerebrumError(f"Request failed: {e}")
    
    # -------------------- CHAT --------------------
    
    async def chat(
        self,
        message: str,
        *,
        model: str = "gpt-3.5-turbo",
        system: str = "You are a helpful assistant.",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        provider: str = "openai"
    ) -> ChatResponse:
        """Send a chat message.
        
        Args:
            message: The message to send
            model: Model to use (gpt-3.5-turbo, gpt-4, etc.)
            system: System prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            provider: AI provider (openai, anthropic, groq)
        
        Returns:
            ChatResponse with .text, .tokens_used, .model
        
        Example:
            >>> response = await client.chat("Hello!")
            >>> print(response.text)
            "Hello! How can I help you today?"
        """
        result = await self._request("POST", "/chat", json={
            "message": message,
            "model": model,
            "system": system,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "provider": provider,
        })
        return ChatResponse(result)
    
    async def chat_stream(
        self,
        message: str,
        *,
        model: str = "gpt-3.5-turbo",
        system: str = "You are a helpful assistant.",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        provider: str = "openai"
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream a chat response token by token.
        
        Args:
            message: The message to send
            model: Model to use
            system: System prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            provider: AI provider
        
        Yields:
            StreamChunk objects with .text and .done attributes
        
        Example:
            >>> async for chunk in client.chat_stream("Tell me a story"):
            ...     print(chunk.text, end="", flush=True)
            Once upon a time...
        """
        client = self._get_client()
        
        async with client.stream(
            "POST",
            "/chat/stream",
            json={
                "message": message,
                "model": model,
                "system": system,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "provider": provider,
            }
        ) as response:
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk_data = json.loads(data)
                        yield StreamChunk(chunk_data)
                    except json.JSONDecodeError:
                        continue
    
    # Convenience accessor for streaming
    @property
    def stream(self):
        """Access streaming methods."""
        return _StreamingAccessor(self)
    
    # -------------------- BLOCKS --------------------
    
    async def list_blocks(self) -> List[Dict[str, Any]]:
        """List all available blocks for your tier.
        
        Returns:
            List of block definitions with name, description, capabilities
        
        Example:
            >>> blocks = await client.list_blocks()
            >>> for block in blocks:
            ...     print(f"{block['name']}: {block['description']}")
        """
        result = await self._request("GET", "/blocks")
        return result.get("blocks", [])
    
    async def execute(
        self,
        block: str,
        input_data: Any,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a single block.
        
        Args:
            block: Block name (chat, pdf, ocr, etc.)
            input_data: Input for the block
            params: Optional parameters
        
        Returns:
            Block execution result
        
        Example:
            >>> result = await client.execute("pdf", "document.pdf", {"extract": "text"})
            >>> print(result["text"])
        """
        return await self._request("POST", "/execute", json={
            "block": block,
            "input": input_data,
            "params": params or {}
        })
    
    async def chain(self, steps: List[Dict[str, Any]], initial_input: Any) -> Dict[str, Any]:
        """Execute a chain of blocks.
        
        Args:
            steps: List of {block: str, params: dict}
            initial_input: Starting input for the chain
        
        Returns:
            Chain execution result with final_output and step_results
        
        Example:
            >>> result = await client.chain([
            ...     {"block": "pdf", "params": {"extract": "text"}},
            ...     {"block": "chat", "params": {"prompt": "Summarize:"}}
            ... ], "document.pdf")
        """
        return await self._request("POST", "/chain", json={
            "steps": steps,
            "initial_input": initial_input
        })
    
    # -------------------- VECTOR SEARCH --------------------
    
    async def vector_add(
        self,
        documents: List[Dict[str, Any]],
        collection: str = "default"
    ) -> Dict[str, Any]:
        """Add documents to vector search.
        
        Args:
            documents: List of {text: str, metadata: dict} objects
            collection: Collection name
        
        Example:
            >>> await client.vector_add([
            ...     {"text": "Hello world", "metadata": {"source": "example"}}
            ... ], collection="docs")
        """
        return await self._request("POST", "/vector/add", json={
            "documents": documents,
            "collection": collection
        })
    
    async def vector_search(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search vector database.
        
        Args:
            query: Search query
            collection: Collection name
            top_k: Number of results
        
        Returns:
            List of matching documents with similarity scores
        
        Example:
            >>> results = await client.vector_search("AI technology", top_k=3)
            >>> for doc in results:
            ...     print(f"{doc['score']}: {doc['text'][:100]}")
        """
        result = await self._request("POST", "/vector/search", json={
            "query": query,
            "collection": collection,
            "top_k": top_k
        })
        return result.get("results", [])
    
    # -------------------- USAGE --------------------
    
    async def usage(self, days: int = 30) -> Dict[str, Any]:
        """Get usage statistics for your API key.
        
        Args:
            days: Number of days to look back
        
        Returns:
            Usage statistics including requests, tokens, limits
        
        Example:
            >>> stats = await client.usage()
            >>> print(f"Used {stats['total_requests']} of {stats['limits']['requests']}")
        """
        # Extract key ID from the API key (cb_<id>_<secret>)
        key_id = self.api_key.split("_")[1] if "_" in self.api_key else "unknown"
        return await self._request("GET", f"/keys/{key_id}/usage", params={"days": days})
    
    async def health(self) -> Dict[str, Any]:
        """Check API health status.
        
        Returns:
            Health status, version, blocks available
        """
        return await self._request("GET", "/health")
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class _StreamingAccessor:
    """Helper class for accessing streaming methods."""
    
    def __init__(self, client: Cerebrum):
        self._client = client
    
    async def chat(self, *args, **kwargs) -> AsyncGenerator[StreamChunk, None]:
        """Stream chat responses."""
        async for chunk in self._client.chat_stream(*args, **kwargs):
            yield chunk


# Alias for backward compatibility
CerebrumClient = Cerebrum
