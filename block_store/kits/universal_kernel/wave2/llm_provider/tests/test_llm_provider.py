"""Tests for the neutral LLM provider sub-kit."""

import pytest

from block_store.kits.universal_kernel.wave2.llm_provider import (
    LLMConfigurationError,
    OpenAIProvider,
    get_provider,
)


def test_stub_provider_returns_coherent_response():
    provider = get_provider("stub")
    completion = provider.complete("Question: What is the capital of France?")
    assert "Stub answer" in completion.text
    assert completion.honesty == "deterministic_stub"
    assert completion.model == "deterministic-stub-v1"
    assert completion.usage["total_tokens"] > 0


def test_stub_provider_includes_usage_metadata():
    provider = get_provider("stub")
    completion = provider.complete("hello world")
    assert "prompt_tokens" in completion.usage
    assert "completion_tokens" in completion.usage
    assert "total_tokens" in completion.usage
    assert "cost_usd" in completion.usage


def test_stub_provider_is_deterministic():
    provider = get_provider("stub")
    c1 = provider.complete("repeat me")
    c2 = provider.complete("repeat me")
    assert c1.text == c2.text


def test_openai_provider_requires_api_key():
    with pytest.raises(LLMConfigurationError):
        OpenAIProvider(api_key=None)


def test_factory_unknown_provider():
    with pytest.raises(LLMConfigurationError):
        get_provider("unknown")
