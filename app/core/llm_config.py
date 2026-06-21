"""LLM provider selection — shared by chat block and agent runtime shims."""

from __future__ import annotations

import os
from typing import Dict

QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_DEFAULT_MODEL = "qwen-plus"

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_DEFAULT_MODEL = "deepseek-chat"

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"

OLLAMA_DEFAULT_URL = "http://localhost:11434/v1/chat/completions"
OLLAMA_DEFAULT_MODEL = "qwen2.5:7b-instruct"


def _llm_config() -> Dict[str, str]:
    """Pick the active LLM provider's URL + env-key + default model.

    Priority:
      1. Explicit LLM_PROVIDER env var.
      2. Qwen (DashScope) if QWEN_API_KEY is set.
      3. Groq if GROQ_API_KEY is set.
      4. DeepSeek if DEEPSEEK_API_KEY is set.
      5. Ollama if OLLAMA_URL is set or localhost is reachable.
    """
    provider = (os.getenv("LLM_PROVIDER") or "").strip().lower()

    if not provider:
        if os.getenv("QWEN_API_KEY"):
            provider = "qwen"
        elif os.getenv("GROQ_API_KEY"):
            provider = "groq"
        elif os.getenv("DEEPSEEK_API_KEY"):
            provider = "deepseek"
        else:
            provider = "ollama"

    if provider == "qwen":
        return {
            "provider": "qwen",
            "url": os.getenv("QWEN_BASE_URL", QWEN_BASE_URL).rstrip("/"),
            "env_key": "QWEN_API_KEY",
            "default_model": os.getenv("QWEN_MODEL", QWEN_DEFAULT_MODEL),
        }

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
