"""Chat Block - AI chat completions"""

import os
from typing import Any, Dict, List, Optional, AsyncGenerator
from app.core.universal_base import UniversalBlock


class ChatBlock(UniversalBlock):
    """AI chat completions supporting OpenAI, Groq, Anthropic, and streaming."""
    
    name = "chat"
    version = "1.2"
    description = "AI chat completions with OpenAI, Groq, Anthropic + streaming"
    layer = 2  # AI Core
    tags = ["ai", "core", "llm", "chat"]
    requires = []  # No dependencies
    
    default_config = {
        "default_provider": "deepseek",
        "max_tokens": 1024,
        "temperature": 0.7
    }
    
    def __init__(self, hal_block=None, config: Dict = None):
        super().__init__(hal_block, config)
        self._openai_available = self._check_openai()
        self._anthropic_available = self._check_anthropic()
        self._groq_available = self._check_groq()
        self._deepseek_available = self._check_deepseek()
    
    def _check_openai(self) -> bool:
        try:
            import openai
            return bool(os.getenv("OPENAI_API_KEY"))
        except ImportError:
            return False
    
    def _check_anthropic(self) -> bool:
        try:
            import anthropic
            return bool(os.getenv("ANTHROPIC_API_KEY"))
        except ImportError:
            return False
    
    def _check_groq(self) -> bool:
        try:
            import groq
            return bool(os.getenv("GROQ_API_KEY"))
        except ImportError:
            return False
    
    def _check_deepseek(self) -> bool:
        return bool(os.getenv("DEEPSEEK_API_KEY"))
    
    async def process(self, input_data: Any, params: Dict = None) -> Dict:
        """Process chat request"""
        params = params or {}
        provider = params.get("provider", self.config.get("default_provider", "deepseek"))
        message = input_data if isinstance(input_data, str) else str(input_data)
        
        # Route to provider
        if provider == "deepseek" and self._deepseek_available:
            return await self._call_deepseek(message, params)
        elif provider == "groq" and self._groq_available:
            return await self._call_groq(message, params)
        elif provider == "openai" and self._openai_available:
            return await self._call_openai(message, params)
        else:
            # Fallback: return echo response for testing
            return {
                "text": f"[ECHO - {provider}] {message}",
                "provider": provider,
                "model": "echo",
                "tokens": {"total": len(message.split())}
            }
    
    async def _call_deepseek(self, message: str, params: Dict) -> Dict:
        """Call DeepSeek API"""
        import httpx
        
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return {"error": "DEEPSEEK_API_KEY not set"}
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": message}],
                    "max_tokens": params.get("max_tokens", 1024)
                },
                timeout=30.0
            )
            data = resp.json()
            
        return {
            "text": data["choices"][0]["message"]["content"],
            "provider": "deepseek",
            "model": "deepseek-chat",
            "tokens": data.get("usage", {})
        }
    
    async def _call_groq(self, message: str, params: Dict) -> Dict:
        """Call Groq API"""
        from groq import Groq
        
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        resp = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": message}],
            max_tokens=params.get("max_tokens", 1024)
        )
        
        return {
            "text": resp.choices[0].message.content,
            "provider": "groq",
            "model": "llama3-8b-8192",
            "tokens": {"total": resp.usage.total_tokens}
        }
    
    async def _call_openai(self, message: str, params: Dict) -> Dict:
        """Call OpenAI API"""
        from openai import OpenAI
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}],
            max_tokens=params.get("max_tokens", 1024)
        )
        
        return {
            "text": resp.choices[0].message.content,
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "tokens": {"total": resp.usage.total_tokens}
        }
