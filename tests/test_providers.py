import os

import pytest

from darija_eval_set.providers import MockProvider, ProviderError, provider_from_env
from darija_eval_set.schema import Item


def _item() -> Item:
    return Item.model_validate(
        {
            "id": "qa-001",
            "category": "qa",
            "prompt": "شنو هي عاصمة المغرب؟",
            "expected": ["الرباط"],
            "scoring": "normalized",
            "languages": ["ary"],
            "review_status": "draft",
        }
    )


def test_mock_is_deterministic() -> None:
    provider = MockProvider(pass_rate_pct=70)
    a = provider.complete(_item())
    b = provider.complete(_item())
    assert a.text == b.text
    assert a.provider == "mock"


def test_mock_pass_rate_bounds() -> None:
    with pytest.raises(ValueError, match="pass_rate_pct"):
        MockProvider(pass_rate_pct=101)


def test_provider_from_env_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DARIJA_EVAL_PROVIDER", "mock")
    provider = provider_from_env()
    assert isinstance(provider, MockProvider)


def test_provider_from_env_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DARIJA_EVAL_PROVIDER", "nope")
    with pytest.raises(ValueError, match="unknown"):
        provider_from_env()


def test_openai_compat_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DARIJA_EVAL_PROVIDER", "openai_compat")
    monkeypatch.delenv("DARIJA_EVAL_API_KEY", raising=False)
    with pytest.raises(ValueError, match="API_KEY"):
        provider_from_env()


def test_openai_compat_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DARIJA_EVAL_PROVIDER", "openai_compat")
    monkeypatch.setenv("DARIJA_EVAL_API_KEY", "sk-test")
    monkeypatch.setenv("DARIJA_EVAL_BASE_URL", "http://127.0.0.1:9/v1/chat/completions")

    import urllib.error
    import urllib.request

    def boom(*_args: object, **_kwargs: object) -> object:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    provider = provider_from_env()
    with pytest.raises(ProviderError):
        provider.complete(_item())


def test_default_provider_is_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DARIJA_EVAL_PROVIDER", raising=False)
    assert os.environ.get("DARIJA_EVAL_PROVIDER") is None
    assert isinstance(provider_from_env(), MockProvider)
