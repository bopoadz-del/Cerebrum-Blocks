"""Neutral LLM provider: deterministic stub + optional OpenAI provider."""

from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class LLMConfigurationError(Exception):
    """Raised when a configured LLM provider cannot be initialized."""


@dataclass
class Completion:
    """Neutral LLM completion result."""

    text: str
    model: str
    usage: Dict[str, Any]
    honesty: str


class LLMProvider(ABC):
    """Abstract LLM provider."""

    model_name: str = "unknown"

    @abstractmethod
    def complete(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 256,
    ) -> Completion:
        raise NotImplementedError

    def _approximate_tokens(self, text: str) -> int:
        """Rough token count: ~4 characters per token on average."""
        return max(1, len(text) // 4)


class DeterministicStubProvider(LLMProvider):
    """Deterministic LLM stub that echoes or patterns from the prompt."""

    model_name = "deterministic-stub-v1"
    COST_PER_1K_TOKENS = 0.0

    def complete(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 256,
    ) -> Completion:
        prompt_text = (prompt or "").strip()
        text = self._pattern_response(prompt_text, max_tokens)
        prompt_tokens = self._approximate_tokens(prompt_text)
        completion_tokens = self._approximate_tokens(text)
        total_tokens = prompt_tokens + completion_tokens
        cost = (total_tokens / 1000.0) * self.COST_PER_1K_TOKENS
        return Completion(
            text=text,
            model=self.model_name,
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost_usd": round(cost, 6),
            },
            honesty="deterministic_stub",
        )

    def _pattern_response(self, prompt: str, max_tokens: int) -> str:
        # Extract a question-like sentence and echo it as a stub answer.
        lower = prompt.lower()
        if "question:" in lower:
            tail = prompt.split("Question:", 1)[-1].strip()
            return self._cap("Stub answer for: " + tail.split("\n")[0], max_tokens)
        if "?" in prompt:
            question = prompt.split("?")[0].strip() + "?"
            return self._cap("Stub answer for: " + question, max_tokens)
        # Return the first sentence or a fixed fallback.
        first = re.split(r"[.\n]", prompt)[0].strip()
        return self._cap("Stub completion: " + first, max_tokens)

    @staticmethod
    def _cap(text: str, max_tokens: int) -> str:
        # Rough cap at ~4 chars per token.
        max_chars = max_tokens * 4
        if len(text) > max_chars:
            return text[:max_chars].rsplit(" ", 1)[0] + "..."
        return text


class OpenAIProvider(LLMProvider):
    """OpenAI provider; fails closed when OPENAI_API_KEY is missing."""

    model_name = "gpt-4o-mini"
    COST_PROMPT_PER_1K = 0.005
    COST_COMPLETION_PER_1K = 0.015

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise LLMConfigurationError("OPENAI_API_KEY is required")

    def complete(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 256,
    ) -> Completion:
        # Neutral stub: real implementation would call the OpenAI API.
        raise NotImplementedError("OpenAI completion call is not implemented in this neutral kit")


def get_provider(provider_id: str = "stub", api_key: Optional[str] = None) -> LLMProvider:
    """Factory for the configured LLM provider."""
    if provider_id == "stub":
        return DeterministicStubProvider()
    if provider_id == "openai":
        return OpenAIProvider(api_key=api_key)
    raise LLMConfigurationError(f"unknown provider_id: {provider_id!r}")
