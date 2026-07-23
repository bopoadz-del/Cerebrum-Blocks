"""Tests for the Moonshot (Kimi) LLM provider sub-kit module.

All tests use a fake transport: no network access, no API key required.
"""

import json

import pytest

from block_store.kits.universal_kernel.wave2.llm_provider import (
    LLMConfigurationError,
)
from block_store.kits.universal_kernel.wave2.llm_provider.moonshot import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_TOKENS_FLOOR,
    DEFAULT_MODEL,
    MoonshotAPIError,
    MoonshotProvider,
    get_moonshot_provider,
)


def _fake_response(text="hello from kimi", model=DEFAULT_MODEL):
    return {
        "choices": [{"message": {"role": "assistant", "content": text}}],
        "model": model,
        "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
    }


class RecordingTransport:
    """Fake transport that records the request and returns a canned response."""

    def __init__(self, response=None):
        self.response = response if response is not None else _fake_response()
        self.calls = []

    def __call__(self, url, body, headers, timeout):
        self.calls.append({"url": url, "body": body, "headers": headers, "timeout": timeout})
        return self.response


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for var in ("MOONSHOT_API_KEY", "MOONSHOT_MODEL", "MOONSHOT_BASE_URL"):
        monkeypatch.delenv(var, raising=False)


def test_moonshot_requires_api_key():
    with pytest.raises(LLMConfigurationError):
        MoonshotProvider(api_key=None)


def test_moonshot_accepts_env_key(monkeypatch):
    monkeypatch.setenv("MOONSHOT_API_KEY", "sk-test-env")
    provider = MoonshotProvider(transport=RecordingTransport())
    assert provider.api_key == "sk-test-env"
    assert provider.model_name == DEFAULT_MODEL
    assert provider.base_url == DEFAULT_BASE_URL


def test_moonshot_forces_temperature_one_and_token_floor():
    transport = RecordingTransport()
    provider = MoonshotProvider(api_key="sk-test", transport=transport)
    provider.complete("hi", temperature=0.0, max_tokens=20)
    body = transport.calls[0]["body"]
    # kimi-k3 (reasoning model) accepts only temperature=1.
    assert body["temperature"] == 1.0
    # Tiny max_tokens is raised to the reasoning-token floor.
    assert body["max_tokens"] == DEFAULT_MAX_TOKENS_FLOOR
    assert body["model"] == DEFAULT_MODEL
    assert body["messages"][0]["content"] == "hi"
    assert transport.calls[0]["headers"]["Authorization"] == "Bearer sk-test"
    assert transport.calls[0]["url"] == DEFAULT_BASE_URL


def test_moonshot_respects_larger_max_tokens():
    transport = RecordingTransport()
    provider = MoonshotProvider(api_key="sk-test", transport=transport)
    provider.complete("hi", max_tokens=1024)
    assert transport.calls[0]["body"]["max_tokens"] == 1024


def test_moonshot_parses_completion_and_marks_live_honesty():
    transport = RecordingTransport(_fake_response(text="grounded answer [1]"))
    provider = MoonshotProvider(api_key="sk-test", transport=transport)
    completion = provider.complete("question?")
    assert completion.text == "grounded answer [1]"
    assert completion.model == DEFAULT_MODEL
    assert completion.honesty == "live_moonshot"
    assert completion.usage == {
        "prompt_tokens": 11,
        "completion_tokens": 7,
        "total_tokens": 18,
    }


def test_moonshot_empty_content_fails_closed():
    transport = RecordingTransport(_fake_response(text=""))
    provider = MoonshotProvider(api_key="sk-test", transport=transport)
    with pytest.raises(MoonshotAPIError):
        provider.complete("hi")


def test_moonshot_missing_choices_fails_closed():
    transport = RecordingTransport(response={"choices": [], "usage": {}})
    provider = MoonshotProvider(api_key="sk-test", transport=transport)
    with pytest.raises(MoonshotAPIError):
        provider.complete("hi")


def test_moonshot_env_overrides_model_and_base_url(monkeypatch):
    monkeypatch.setenv("MOONSHOT_MODEL", "kimi-k2.6")
    monkeypatch.setenv("MOONSHOT_BASE_URL", "https://example.test/v1/chat/completions")
    transport = RecordingTransport()
    provider = MoonshotProvider(api_key="sk-test", transport=transport)
    provider.complete("hi")
    assert provider.model_name == "kimi-k2.6"
    assert transport.calls[0]["url"] == "https://example.test/v1/chat/completions"
    assert transport.calls[0]["body"]["model"] == "kimi-k2.6"


def test_get_moonshot_provider_helper():
    provider = get_moonshot_provider(api_key="sk-test", transport=RecordingTransport())
    assert isinstance(provider, MoonshotProvider)


def test_default_transport_sends_json_body(monkeypatch):
    """The urllib transport posts the exact JSON body to the URL (mocked urlopen)."""
    import io
    from block_store.kits.universal_kernel.wave2.llm_provider import moonshot

    captured = {}

    class FakeResp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(req, timeout=0):
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data.decode("utf-8"))
        captured["auth"] = req.headers.get("Authorization")
        return FakeResp(json.dumps(_fake_response()).encode("utf-8"))

    monkeypatch.setattr(moonshot.urllib.request, "urlopen", fake_urlopen)
    provider = MoonshotProvider(api_key="sk-test")
    completion = provider.complete("ping")
    assert completion.honesty == "live_moonshot"
    assert captured["url"] == DEFAULT_BASE_URL
    assert captured["body"]["messages"][0]["content"] == "ping"
    assert captured["auth"] == "Bearer sk-test"
