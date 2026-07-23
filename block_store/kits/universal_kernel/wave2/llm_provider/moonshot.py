"""Moonshot (Kimi) LLM provider: real OpenAI-compatible completion calls.

Fail-closed by construction:
- MOONSHOT_API_KEY env var (or explicit api_key) is required at init.
- No key -> LLMConfigurationError, never a silent stub.
- Empty completion content from the API -> MoonshotAPIError, never silent "".

Kimi model quirks handled here (discovered against the live API, 2026-07-23):
- kimi-k3 is a reasoning model: it accepts ONLY temperature=1.
- Reasoning tokens consume the max_tokens budget; requests with a tiny
  max_tokens can return empty content. A floor (default 300) is enforced.
- International endpoint is https://api.moonshot.ai (the .cn endpoint
  rejects international keys with 401).

Stdlib only (urllib), matching the neutral kit's zero-dependency rule.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, Optional

from .code import Completion, LLMConfigurationError, LLMProvider

DEFAULT_BASE_URL = "https://api.moonshot.ai/v1/chat/completions"
DEFAULT_MODEL = "kimi-k3"
# kimi-k3 only accepts temperature=1 (reasoning model).
KIMI_K3_FORCED_TEMPERATURE = 1.0
# Reasoning models burn reasoning tokens inside the max_tokens budget;
# below this floor the API can return empty content.
DEFAULT_MAX_TOKENS_FLOOR = 300
DEFAULT_TIMEOUT_SECONDS = 120.0


class MoonshotAPIError(Exception):
    """Raised when the Moonshot API call fails or returns unusable content."""


# transport(url, body, headers, timeout_seconds) -> parsed JSON dict
Transport = Callable[[str, Dict[str, Any], Dict[str, str], float], Dict[str, Any]]


def _urllib_transport(
    url: str, body: Dict[str, Any], headers: Dict[str, str], timeout: float
) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise MoonshotAPIError(f"Moonshot API HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise MoonshotAPIError(f"Moonshot API connection error: {exc.reason}") from exc


class MoonshotProvider(LLMProvider):
    """Moonshot (Kimi) provider; fails closed when MOONSHOT_API_KEY is missing."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_tokens_floor: int = DEFAULT_MAX_TOKENS_FLOOR,
        transport: Optional[Transport] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("MOONSHOT_API_KEY")
        if not self.api_key:
            raise LLMConfigurationError("MOONSHOT_API_KEY is required")
        self.model_name = model or os.getenv("MOONSHOT_MODEL") or DEFAULT_MODEL
        self.base_url = (
            base_url or os.getenv("MOONSHOT_BASE_URL") or DEFAULT_BASE_URL
        )
        self.timeout = float(timeout)
        self.max_tokens_floor = int(max_tokens_floor)
        self._transport = transport or _urllib_transport

    def complete(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 256,
    ) -> Completion:
        effective_max_tokens = max(int(max_tokens), self.max_tokens_floor)
        body: Dict[str, Any] = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            # kimi-k3 accepts only temperature=1; the caller's value is
            # intentionally overridden for reasoning-model compatibility.
            "temperature": KIMI_K3_FORCED_TEMPERATURE,
            "max_tokens": effective_max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        resp = self._transport(self.base_url, body, headers, self.timeout)

        choices = resp.get("choices") or []
        content = ""
        if choices:
            content = (choices[0].get("message") or {}).get("content") or ""
        if not content.strip():
            raise MoonshotAPIError(
                "Moonshot API returned empty completion content "
                f"(model={self.model_name}, max_tokens={effective_max_tokens}); "
                "raise max_tokens above the reasoning-token floor"
            )
        usage_raw = resp.get("usage") or {}
        usage: Dict[str, Any] = {
            "prompt_tokens": usage_raw.get("prompt_tokens"),
            "completion_tokens": usage_raw.get("completion_tokens"),
            "total_tokens": usage_raw.get("total_tokens"),
        }
        return Completion(
            text=content,
            model=resp.get("model") or self.model_name,
            usage=usage,
            honesty="live_moonshot",
        )


def get_moonshot_provider(api_key: Optional[str] = None, **kwargs: Any) -> MoonshotProvider:
    """Explicit constructor helper (factory dispatch in code.py stays pin-protected)."""
    return MoonshotProvider(api_key=api_key, **kwargs)
