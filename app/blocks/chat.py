"""Chat Block - AI Chat with DeepSeek API and Typed Schema"""

import json
import os
import httpx
from typing import Any, Dict, Optional
from app.core.typed_block import TypedBlock, Schema, ContentType


class ChatBlock(TypedBlock):
    """AI chat completions with DeepSeek API and typed I/O"""

    name = "chat"
    version = "2.0.0"
    description = "AI chat completions with DeepSeek API"
    layer = 2
    tags = ["ai", "core", "llm", "chat", "typed"]
    requires = []

    default_config = {
        "default_provider": "deepseek",
        "max_tokens": 2048,
        "temperature": 0.7
    }

    # Type schemas for chain validation
    input_schema = Schema(
        content_type=ContentType.TEXT,
        required_fields=[],  # Can be string or {text: ...}
        optional_fields=["text", "message", "context"],
        format_hints={"max_length": 100000}
    )

    output_schema = Schema(
        content_type=ContentType.TEXT,
        required_fields=["text"],
        optional_fields=["provider", "model", "tokens", "status"],
        format_hints={}
    )

    ui_schema = {
        "input": {
            "type": "text",
            "accept": None,
            "placeholder": "Ask anything...",
            "multiline": True
        },
        "output": {
            "type": "text",
            "fields": [
                {"name": "text", "type": "markdown", "label": "Response"}
            ]
        },
        "quick_actions": [
            {"icon": "💡", "label": "Explain", "prompt": "Explain this in simple terms"},
            {"icon": "📝", "label": "Summarize", "prompt": "Summarize the key points"}
        ]
    }

    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Process chat request"""
        params = params or {}
        
        # Normalize input to string
        if isinstance(input_data, str):
            message = input_data
        elif isinstance(input_data, dict):
            message = input_data.get("text") or input_data.get("message") or str(input_data)
        else:
            message = str(input_data)

        # Get API key from environment or use hardcoded fallback
        api_key = os.getenv("DEEPSEEK_API_KEY") or "sk-62229915230e448b82ea08550d11fa86"
        if not api_key:
            return {
                "status": "error",
                "error": "DEEPSEEK_API_KEY not configured."
            }

        model = params.get("model", "deepseek-chat")
        max_tokens = params.get("max_tokens", self.config.get("max_tokens", 2048))
        temperature = params.get("temperature", self.config.get("temperature", 0.7))
        stream = params.get("stream", False)

        if stream:
            async def _stream_generator():
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream(
                        "POST",
                        "https://api.deepseek.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model,
                            "messages": [{"role": "user", "content": message}],
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                            "stream": True,
                        }
                    ) as response:
                        if response.status_code != 200:
                            error_text = await response.aread()
                            yield json.dumps({
                                "type": "error",
                                "message": f"DeepSeek API error (HTTP {response.status_code}): {error_text[:200]}"
                            })
                            return

                        async for line in response.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            data = line[6:]
                            if data == "[DONE]":
                                continue
                            try:
                                chunk = json.loads(data)
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except Exception:
                                continue

            return {
                "status": "success",
                "text": "",
                "provider": "deepseek",
                "model": model,
                "stream": _stream_generator(),
            }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": message}],
                        "max_tokens": max_tokens,
                        "temperature": temperature
                    }
                )

                if response.status_code != 200:
                    error_text = response.text
                    return {
                        "status": "error",
                        "error": f"DeepSeek API error (HTTP {response.status_code}): {error_text[:200]}"
                    }

                data = response.json()

                return {
                    "status": "success",
                    "text": data["choices"][0]["message"]["content"],
                    "provider": "deepseek",
                    "model": model,
                    "tokens": data.get("usage", {})
                }

        except httpx.TimeoutException:
            return {
                "status": "error",
                "error": "Request timed out. The AI service is taking too long to respond."
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Chat failed: {str(e)}"
            }
