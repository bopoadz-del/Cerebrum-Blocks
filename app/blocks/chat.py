"""Chat Block - AI chat completions with OpenAI, Groq, Anthropic + streaming."""

import os
from typing import Any, Dict, List, Optional, AsyncGenerator
from app.core.block import BaseBlock, BlockConfig

class ChatBlock(BaseBlock):
    """AI chat completions supporting OpenAI, Groq, Anthropic, and streaming."""

    def __init__(self):
        super().__init__(BlockConfig(
            name="chat",
            version="1.2",
            description="AI chat completions with OpenAI, Groq, Anthropic + streaming. Chains perfectly with PDF/OCR/etc.",
            requires_api_key=True,
            supported_inputs=["text", "messages", "file_result"],
            supported_outputs=["text", "stream", "tokens", "model"]
        ))
        self._openai_available = self._check_openai()
        self._anthropic_available = self._check_anthropic()
        self._groq_available = self._check_groq()
        self._deepseek_available = self._check_deepseek()

    def _check_openai(self) -> bool:
        try:
            import openai
            return True
        except ImportError:
            return False

    def _check_anthropic(self) -> bool:
        try:
            import anthropic
            return True
        except ImportError:
            return False

    def _check_groq(self) -> bool:
        try:
            import groq
            return True
        except ImportError:
            return False

    def _check_deepseek(self) -> bool:
        try:
            import openai  # DeepSeek uses OpenAI-compatible API
            return True
        except ImportError:
            return False

    async def process(self, input_data: Any, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main processing logic — only part you ever change per block."""
        params = params or {}
        provider = params.get("provider", "deepseek")    # default to cheapest
        model = params.get("model", "llama-3.3-70b-versatile")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 2048)
        stream = params.get("stream", False)
        system = params.get("system", "You are a helpful assistant.")

        # Build messages (works with text, list, or previous block result)
        messages = self._build_messages(input_data, params.get("prompt", ""), system)

        result = {
            "provider": provider,
            "model": model,
            "messages_sent": len(messages),
        }

        if stream:
            result["stream"] = self._get_stream_generator(provider, messages, model, max_tokens, temperature)
            result["text"] = ""
            return result

        # Non-streaming (cheapest first)
        if provider == "deepseek" and self._deepseek_available:
            response = await self._call_deepseek(messages, model or "deepseek-chat", max_tokens, temperature)
        elif provider == "groq" and self._groq_available:
            response = await self._call_groq(messages, model, max_tokens, temperature)
        elif provider == "openai" and self._openai_available:
            response = await self._call_openai(messages, model, max_tokens, temperature)
        elif provider == "anthropic" and self._anthropic_available:
            response = await self._call_anthropic(messages, model, max_tokens, temperature)
        else:
            response = {"text": f"[Provider {provider} not available. Install package or set API key.]", "confidence": 0.3}

        result.update(response)
        return result

    def _build_messages(self, input_data: Any, prompt: str, system: str) -> List[Dict]:
        messages = [{"role": "system", "content": system}]

        if isinstance(input_data, list):
            messages.extend(input_data)
        elif isinstance(input_data, dict):
            if "text" in input_data:
                messages.append({"role": "user", "content": input_data["text"]})
            elif "result" in input_data and isinstance(input_data["result"], dict):
                text = input_data["result"].get("text", input_data["result"].get("extracted_text", ""))
                if text:
                    messages.append({"role": "user", "content": text})
            elif "messages" in input_data:
                messages.extend(input_data["messages"])
        elif isinstance(input_data, str):
            messages.append({"role": "user", "content": input_data})

        if prompt:
            messages.append({"role": "user", "content": prompt})

        return messages

    def _get_stream_generator(self, provider: str, messages: List[Dict], model: str, max_tokens: int, temperature: float):
        """Returns async generator for streaming."""
        if provider == "deepseek" and self._deepseek_available:
            return self._stream_deepseek(messages, model, max_tokens, temperature)
        elif provider == "groq" and self._groq_available:
            return self._stream_groq(messages, model, max_tokens, temperature)
        elif provider == "openai" and self._openai_available:
            return self._stream_openai(messages, model, max_tokens, temperature)
        elif provider == "anthropic" and self._anthropic_available:
            return self._stream_anthropic(messages, model, max_tokens, temperature)
        else:
            async def mock_stream():
                text = "[Mock stream - provider not available]"
                for word in text.split():
                    yield {"text": word + " ", "done": False}
                yield {"text": "", "done": True}
            return mock_stream()

    # ==================== PROVIDER CALLS ====================

    async def _call_deepseek(self, messages: List[Dict], model: str, max_tokens: int, temperature: float) -> Dict:
        """Call DeepSeek API - cheapest provider ($0.14/M tokens)."""
        import openai
        client = openai.AsyncOpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        try:
            response = await client.chat.completions.create(
                model=model or "deepseek-chat",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return {
                "text": response.choices[0].message.content,
                "finish_reason": response.choices[0].finish_reason,
                "tokens_prompt": response.usage.prompt_tokens,
                "tokens_completion": response.usage.completion_tokens,
                "tokens_total": response.usage.total_tokens,
                "confidence": 0.96
            }
        except Exception as e:
            return {"text": f"[DeepSeek Error: {str(e)}]", "confidence": 0.0}

    async def _call_groq(self, messages: List[Dict], model: str, max_tokens: int, temperature: float) -> Dict:
        import groq
        client = groq.AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return {
                "text": response.choices[0].message.content,
                "finish_reason": response.choices[0].finish_reason,
                "tokens_prompt": response.usage.prompt_tokens,
                "tokens_completion": response.usage.completion_tokens,
                "tokens_total": response.usage.total_tokens,
                "confidence": 0.98
            }
        except Exception as e:
            return {"text": f"[Groq Error: {str(e)}]", "confidence": 0.0}

    async def _call_openai(self, messages: List[Dict], model: str, max_tokens: int, temperature: float) -> Dict:
        import openai
        client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return {
                "text": response.choices[0].message.content,
                "finish_reason": response.choices[0].finish_reason,
                "tokens_prompt": response.usage.prompt_tokens,
                "tokens_completion": response.usage.completion_tokens,
                "tokens_total": response.usage.total_tokens,
                "confidence": 0.95
            }
        except Exception as e:
            return {"text": f"[OpenAI Error: {str(e)}]", "confidence": 0.0}

    async def _call_anthropic(self, messages: List[Dict], model: str, max_tokens: int, temperature: float) -> Dict:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        try:
            system_msg = next((m["content"] for m in messages if m["role"] == "system"), None)
            chat_messages = [m for m in messages if m["role"] != "system"]
            response = await client.messages.create(
                model=model or "claude-3-haiku-20240307",
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_msg,
                messages=chat_messages
            )
            return {
                "text": response.content[0].text,
                "confidence": 0.97
            }
        except Exception as e:
            return {"text": f"[Anthropic Error: {str(e)}]", "confidence": 0.0}

    # Streaming helpers (similar pattern)

    async def _stream_deepseek(self, messages, model, max_tokens, temperature):
        """Stream from DeepSeek - cheapest provider."""
        import openai
        client = openai.AsyncOpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        try:
            stream = await client.chat.completions.create(
                model=model or "deepseek-chat", messages=messages, max_tokens=max_tokens,
                temperature=temperature, stream=True
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {"text": chunk.choices[0].delta.content, "done": False}
            yield {"text": "", "done": True}
        except Exception as e:
            yield {"text": f"[DeepSeek Stream Error: {str(e)}]", "done": True}

    async def _stream_groq(self, messages, model, max_tokens, temperature):
        import groq
        client = groq.AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        try:
            stream = await client.chat.completions.create(
                model=model, messages=messages, max_tokens=max_tokens,
                temperature=temperature, stream=True
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {"text": chunk.choices[0].delta.content, "done": False}
            yield {"text": "", "done": True}
        except Exception as e:
            yield {"text": f"[Groq Stream Error: {str(e)}]", "done": True}

    async def _stream_openai(self, messages, model, max_tokens, temperature):
        import openai
        client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        try:
            stream = await client.chat.completions.create(
                model=model, messages=messages, max_tokens=max_tokens,
                temperature=temperature, stream=True
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {"text": chunk.choices[0].delta.content, "done": False}
            yield {"text": "", "done": True}
        except Exception as e:
            yield {"text": f"[OpenAI Stream Error: {str(e)}]", "done": True}

    async def _stream_anthropic(self, messages, model, max_tokens, temperature):
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        try:
            system_msg = next((m["content"] for m in messages if m["role"] == "system"), None)
            chat_messages = [m for m in messages if m["role"] != "system"]
            async with client.messages.stream(
                model=model or "claude-3-haiku-20240307",
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_msg,
                messages=chat_messages
            ) as stream:
                async for text in stream.text_stream:
                    yield {"text": text, "done": False}
                yield {"text": "", "done": True}
        except Exception as e:
            yield {"text": f"[Anthropic Stream Error: {str(e)}]", "done": True}
