import json
import urllib.error
import urllib.request
from io import BytesIO
from pathlib import Path
from types import TracebackType
from typing import Any

import pytest
from typer.testing import CliRunner

from darija_eval_set.cache import ResponseCache
from darija_eval_set.cli import app
from darija_eval_set.dataset import load_items
from darija_eval_set.judge import JUDGE_SYSTEM_PROMPT, Judge
from darija_eval_set.providers import (
    MockProvider,
    OpenAICompatProvider,
    Provider,
    ProviderError,
    ProviderResponse,
    provider_from_env,
)
from darija_eval_set.results import build_summary, render_html
from darija_eval_set.runner import run_eval
from darija_eval_set.schema import Item

REPO_DATA = Path(__file__).parent.parent / "data" / "items.jsonl"


def _item() -> Item:
    return load_items(REPO_DATA)[0][0]


def _live(base_url: str = "https://example.test/v1/chat/completions") -> OpenAICompatProvider:
    return OpenAICompatProvider(api_key="sk-test", base_url=base_url, model="m")


def _http_error(code: int, body: bytes = b"x") -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://example.test", code, "err", None, BytesIO(body))  # type: ignore[arg-type]


def _patch_urlopen(monkeypatch: pytest.MonkeyPatch, exc: BaseException) -> None:
    def boom(*_a: object, **_k: object) -> object:
        raise exc

    monkeypatch.setattr(urllib.request, "urlopen", boom)


class FakeResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def read(self) -> bytes:
        return self.body


# providers


@pytest.mark.parametrize(
    "url",
    ["file:///etc/passwd", "ftp://example.test/x", "http://example.test/v1", "not a url", ""],
)
def test_base_url_must_be_https_or_local_http(url: str) -> None:
    with pytest.raises(ValueError, match="DARIJA_EVAL_BASE_URL"):
        _live(url)


@pytest.mark.parametrize("url", ["https://example.test/v1", "http://localhost:8000/v1"])
def test_base_url_accepts_https_and_localhost_http(url: str) -> None:
    assert _live(url).base_url == url


def test_empty_env_values_fall_back_to_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DARIJA_EVAL_PROVIDER", "openai_compat")
    monkeypatch.setenv("DARIJA_EVAL_API_KEY", "sk-test")
    monkeypatch.setenv("DARIJA_EVAL_BASE_URL", "")
    monkeypatch.setenv("DARIJA_EVAL_MODEL", "")
    provider = provider_from_env()
    assert isinstance(provider, OpenAICompatProvider)
    assert provider.model == "gpt-4o-mini"
    assert provider.base_url.startswith("https://api.openai.com")


@pytest.mark.parametrize(
    ("code", "retryable"), [(401, False), (400, False), (429, True), (503, True)]
)
def test_http_status_decides_retryable(
    monkeypatch: pytest.MonkeyPatch, code: int, retryable: bool
) -> None:
    _patch_urlopen(monkeypatch, _http_error(code, b"x" * 2000))
    with pytest.raises(ProviderError) as info:
        _live().complete(_item())
    assert info.value.retryable is retryable
    assert len(str(info.value)) < 600


def test_timeout_and_bad_json_become_provider_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_urlopen(monkeypatch, TimeoutError("timed out"))
    with pytest.raises(ProviderError, match="TimeoutError"):
        _live().complete(_item())

    monkeypatch.setattr(
        urllib.request, "urlopen", lambda *_a, **_k: FakeResponse(b"<html>gateway</html>")
    )
    with pytest.raises(ProviderError, match="not valid JSON"):
        _live().complete(_item())


def test_custom_system_message_is_sent(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: dict[str, Any] = {}
    body = json.dumps({"choices": [{"message": {"content": "YES"}}]}).encode()

    def fake(request: urllib.request.Request, **_k: object) -> FakeResponse:
        assert isinstance(request.data, bytes)
        sent.update(json.loads(request.data))
        return FakeResponse(body)

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    _live().complete(_item(), system="custom system")
    assert sent["messages"][0]["content"] == "custom system"


# judge


def test_live_judge_uses_judge_system_prompt() -> None:
    seen: list[str | None] = []

    class Spy(Provider):
        name = "spy"

        def complete(self, item: Item, *, system: str | None = None) -> ProviderResponse:
            seen.append(system)
            return ProviderResponse(text=" yes, fine", model="m", provider="spy")

    assert Judge(Spy()).accepts(_item(), "whatever")
    assert seen == [JUDGE_SYSTEM_PROMPT]


# cache and runner


def test_corrupt_cache_entry_is_a_miss(tmp_path: Path) -> None:
    cache = ResponseCache(tmp_path)
    (tmp_path / "abc.json").write_text("{truncated", encoding="utf-8")
    assert cache.get("abc") is None
    (tmp_path / "def.json").write_text('{"text": "x"}', encoding="utf-8")
    assert cache.get("def") is None


def test_mock_runs_do_not_share_cache_across_pass_rates(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    high = run_eval(
        dataset=REPO_DATA,
        provider=MockProvider(pass_rate_pct=100),
        output_json=tmp_path / "a.json",
        resume=False,
        cache_dir=cache_dir,
    )
    low = run_eval(
        dataset=REPO_DATA,
        provider=MockProvider(pass_rate_pct=0),
        output_json=tmp_path / "b.json",
        resume=False,
        cache_dir=cache_dir,
    )
    assert high.passed == 150
    assert low.passed == 0
    assert not list(cache_dir.glob("*.json"))


def test_non_retryable_error_is_not_retried(tmp_path: Path) -> None:
    calls: list[int] = []

    class Denied(MockProvider):
        def complete(self, item: Item, *, system: str | None = None) -> ProviderResponse:
            calls.append(1)
            raise ProviderError("HTTP 401", retryable=False)

    with pytest.raises(ProviderError):
        run_eval(
            dataset=REPO_DATA,
            provider=Denied(),
            output_json=tmp_path / "r.json",
            resume=False,
            retries=3,
            backoff_s=0.0,
        )
    assert len(calls) == 1


def test_resume_ignores_results_from_another_provider(tmp_path: Path) -> None:
    out = tmp_path / "results.json"
    run_eval(dataset=REPO_DATA, provider=MockProvider(pass_rate_pct=100), output_json=out)
    data = json.loads(out.read_text(encoding="utf-8"))
    data["provider"], data["model"] = "openai_compat", "gpt-x"
    out.write_text(json.dumps(data), encoding="utf-8")
    again = run_eval(dataset=REPO_DATA, provider=MockProvider(pass_rate_pct=0), output_json=out)
    assert again.passed == 0


def test_resume_reruns_edited_items(tmp_path: Path) -> None:
    out = tmp_path / "results.json"
    run_eval(dataset=REPO_DATA, provider=MockProvider(pass_rate_pct=100), output_json=out)
    data = json.loads(out.read_text(encoding="utf-8"))
    data["items"][0]["expected"] = ["something that is no longer the answer"]
    out.write_text(json.dumps(data), encoding="utf-8")
    again = run_eval(dataset=REPO_DATA, provider=MockProvider(pass_rate_pct=100), output_json=out)
    assert again.items[0].expected == _item().expected
    assert again.items[0].passed


def test_resume_with_unreadable_results_file_fails_cleanly(tmp_path: Path) -> None:
    out = tmp_path / "results.json"
    out.write_text("{truncated", encoding="utf-8")
    with pytest.raises(ValueError, match="--no-resume"):
        run_eval(dataset=REPO_DATA, provider=MockProvider(), output_json=out)
    out.write_text('{"provider": "mock"}', encoding="utf-8")
    with pytest.raises(ValueError, match="--no-resume"):
        run_eval(dataset=REPO_DATA, provider=MockProvider(), output_json=out)


def test_html_output_only_is_written(tmp_path: Path) -> None:
    html = tmp_path / "out.html"
    run_eval(
        dataset=REPO_DATA,
        provider=MockProvider(),
        output_json=tmp_path / "r.json",
        output_html=html,
        resume=False,
    )
    assert html.is_file()


def test_cli_reports_provider_failure_without_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DARIJA_EVAL_PROVIDER", "openai_compat")
    monkeypatch.setenv("DARIJA_EVAL_API_KEY", "sk-test")
    monkeypatch.setenv("DARIJA_EVAL_BASE_URL", "https://example.test/v1")
    _patch_urlopen(monkeypatch, _http_error(401, b"bad key"))
    result = CliRunner().invoke(
        app, ["run", "--output", str(tmp_path / "r.json"), "--no-cache", "--retries", "0"]
    )
    assert result.exit_code == 1
    assert "HTTP 401" in result.output
    assert "Traceback" not in result.output


# results


def test_html_output_escapes_model_name() -> None:
    summary = build_summary(
        provider="openai_compat",
        model="<script>alert(1)</script>",
        dataset="a&b",
        is_mock=False,
        items=[],
    )
    page = render_html(summary)
    assert "<script>" not in page
    assert "&lt;script&gt;" in page
    assert "a&amp;b" in page


# dataset


def test_validate_handles_bom_and_bad_encoding(tmp_path: Path) -> None:
    line = REPO_DATA.read_text(encoding="utf-8").splitlines()[0]
    with_bom = tmp_path / "bom.jsonl"
    with_bom.write_bytes(b"\xef\xbb\xbf" + line.encode("utf-8") + b"\n")
    items, errors = load_items(with_bom)
    assert len(items) == 1
    assert errors == []

    latin = tmp_path / "latin.jsonl"
    latin.write_bytes(b'{"id": "\xe9"}\n')
    _, errors = load_items(latin)
    assert len(errors) == 1
    assert "UTF-8" in errors[0].reason
