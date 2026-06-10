"""LLM provider selection — shared by chat block and agent runtime shims."""

from __future__ import annotations

import os
from typing import Dict

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_DEFAULT_MODEL = "deepseek-chat"

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"

OLLAMA_DEFAULT_URL = "http://localhost:11434/v1/chat/completions"
OLLAMA_DEFAULT_MODEL = "qwen2.5:7b-instruct"


def _llm_config() -> Dict[str, str]:
    """Pick the active LLM provider's URL + env-key + default model."""
    provider = (os.getenv("LLM_PROVIDER") or "").strip().lower()
    if not provider:
        provider = "groq" if os.getenv("GROQ_API_KEY") else "deepseek"
    if provider == "ollama":
        url = os.getenv("OLLAMA_URL", OLLAMA_DEFAULT_URL).rstrip("/")
        if not url.endswith("/v1/chat/completions"):
            if url.endswith("/v1"):
                url = url + "/chat/completions"
            elif "/v1/" not in url:
                url = url + "/v1/chat/completions"
        return {
            "provider": "ollama",
            "url": url,
            "env_key": "",
            "default_model": os.getenv("OLLAMA_MODEL", OLLAMA_DEFAULT_MODEL),
        }
    if provider == "groq":
        return {
            "provider": "groq",
            "url": GROQ_API_URL,
            "env_key": "GROQ_API_KEY",
            "default_model": os.getenv("GROQ_MODEL", GROQ_DEFAULT_MODEL),
        }
    return {
        "provider": "deepseek",
        "url": DEEPSEEK_API_URL,
        "env_key": "DEEPSEEK_API_KEY",
        "default_model": os.getenv("DEEPSEEK_MODEL", DEEPSEEK_DEFAULT_MODEL),
    }
