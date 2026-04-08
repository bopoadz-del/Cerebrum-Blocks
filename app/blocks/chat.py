"""Chat Block - AI chat completions with streaming support."""

import os
from typing import Any, Dict, List, Optional, AsyncGenerator
from app.core.block import BaseBlock, BlockConfig


class ChatBlock(BaseBlock):
    """AI chat completions supporting OpenAI, Anthropic, local models, and streaming."""
    
    def __init__(self):
        super().__init__(BlockConfig(
            name="chat",
            version="1.1",
            description="AI chat completions with OpenAI, Anthropic, local models, and streaming",
            requires_api_key=True,
            supported_inputs=["text", "messages"],
            supported_outputs=["text", "stream"]
        ))
        self._openai_available = self._check_openai()
        self._anthropic_available = self._check_anthropic()
    
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
    
    async def process(self, input_data: Any, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process chat request."""
        params = params or {}
        provider = params.get("provider", "openai")
        model = params.get("model", "gpt-3.5-turbo")
        prompt = params.get("prompt", "")
        system_message = params.get("system", "You are a helpful assistant.")
        max_tokens = params.get("max_tokens", 1000)
        temperature = params.get("temperature", 0.7)
        stream = params.get("stream", False)
        
        messages = self._build_messages(input_data, prompt, system_message)
        
        result = {
            "provider": provider,
            "model": model,
            "messages_sent": len(messages),
        }
        
        if stream:
            # Return a stream generator instead of text
            result["stream"] = self._stream_response(provider, messages, model, max_tokens, temperature)
            result["text"] = ""
            return result
        
        if provider == "openai" and self._openai_available:
            response = await self._call_openai(messages, model, max_tokens, temperature)
            result.update(response)
        elif provider == "anthropic" and self._anthropic_available:
            response = await self._call_anthropic(messages, model, max_tokens, temperature)
            result.update(response)
        elif provider == "mock":
            result["text"] = f"[Mock response] Received: {messages[-1]['content'][:100] if messages else 'No input'}..."
            result["tokens_used"] = 0
            result["confidence"] = 1.0
        else:
            result["text"] = f"[Provider {provider} not available]"
            result["confidence"] = 0.0
        
        return result
    
    def _build_messages(self, input_data: Any, prompt: str, system: str) -> List[Dict]:
        """Build message list from input."""
        messages = [{"role": "system", "content": system}]
        
        if isinstance(input_data, list):
            messages = input_data
        elif isinstance(input_data, dict):
            if "text" in input_data:
                messages.append({"role": "user", "content": input_data["text"]})
            elif "messages" in input_data:
                messages = input_data["messages"]
            elif "result" in input_data and isinstance(input_data["result"], dict):
                text = input_data["result"].get("text", "")
                if text:
                    messages.append({"role": "user", "content": text})
        elif isinstance(input_data, str):
            messages.append({"role": "user", "content": input_data})
        
        if prompt and messages[-1]["role"] != "user":
            messages.append({"role": "user", "content": prompt})
        
        return messages
    
    async def _stream_response(self, provider: str, messages: List[Dict], model: str, max_tokens: int, temperature: float):
        """Generate streaming response chunks."""
        if provider == "openai" and self._openai_available:
            async for chunk in self._stream_openai(messages, model, max_tokens, temperature):
                yield chunk
        elif provider == "anthropic" and self._anthropic_available:
            async for chunk in self._stream_anthropic(messages, model, max_tokens, temperature):
                yield chunk
        else:
            # Mock streaming
            text = f"[Mock stream] Received: {messages[-1]['content'][:100] if messages else 'No input'}..."
            for word in text.split():
                yield {"text": word + " ", "done": False}
            yield {"text": "", "done": True}
    
    async def _stream_openai(self, messages: List[Dict], model: str, max_tokens: int, temperature: float):
        """Stream from OpenAI."""
        import openai
        client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        try:
            stream = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield {"text": delta.content, "done": False}
            yield {"text": "", "done": True}
        except Exception as e:
            yield {"text": f"[OpenAI Error: {str(e)}]", "done": True}
    
    async def _stream_anthropic(self, messages: List[Dict], model: str, max_tokens: int, temperature: float):
        """Stream from Anthropic."""
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        try:
            system_msg = None
            chat_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    chat_messages.append(msg)
            
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
            yield {"text": f"[Anthropic Error: {str(e)}]", "done": True}
    
    async def _call_openai(self, messages: List[Dict], model: str, max_tokens: int, temperature: float) -> Dict:
        """Call OpenAI API."""
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
            return {
                "text": f"[OpenAI Error: {str(e)}]",
                "confidence": 0.0
            }
    
    async def _call_anthropic(self, messages: List[Dict], model: str, max_tokens: int, temperature: float) -> Dict:
        """Call Anthropic API."""
        import anthropic
        
        client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        try:
            system_msg = None
            chat_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    chat_messages.append(msg)
            
            response = await client.messages.create(
                model=model or "claude-3-haiku-20240307",
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_msg,
                messages=chat_messages
            )
            
            return {
                "text": response.content[0].text,
                "stop_reason": response.stop_reason,
                "tokens_input": response.usage.input_tokens,
                "tokens_output": response.usage.output_tokens,
                "confidence": 0.95
            }
        except Exception as e:
            return {
                "text": f"[Anthropic Error: {str(e)}]",
                "confidence": 0.0
            }
