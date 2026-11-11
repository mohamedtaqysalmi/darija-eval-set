import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from darija_eval_set.cache import ResponseCache, cache_key
from darija_eval_set.cli import app
from darija_eval_set.providers import MockProvider, ProviderError, ProviderResponse
from darija_eval_set.runner import run_eval
from darija_eval_set.schema import Category, Item, ReviewStatus, ScoringMethod

runner = CliRunner()
REPO_DATA = Path(__file__).parent.parent / "data" / "items.jsonl"


def _item(id_: str = "qa-001", prompt: str = "شنو؟", expected: list[str] | None = None) -> Item:
    return Item(
        id=id_,
        category=Category.QA,
        prompt=prompt,
        expected=expected or ["الرباط"],
        scoring=ScoringMethod.NORMALIZED,
        languages=["ary"],
        review_status=ReviewStatus.DRAFT,
    )


def test_mock_provider_is_deterministic() -> None:
    p = MockProvider(pass_rate_pct=70)
    item = _item("qa-001")
    a = p.complete(item)
    b = p.complete(item)
    assert a.text == b.text


def test_cache_roundtrip(tmp_path: Path) -> None:
    cache = ResponseCache(tmp_path)
    key = cache_key("mock", "mock-v1", "hello")
    assert cache.get(key) is None
    cache.set(key, ProviderResponse(text="hi", model="mock-v1", provider="mock"))
    got = cache.get(key)
    assert got is not None
    assert got.text == "hi"


def test_run_eval_writes_results_and_tables(tmp_path: Path) -> None:
    out = tmp_path / "results.json"
    md = tmp_path / "results.md"
    html = tmp_path / "results.html"
    cache = tmp_path / "cache"
    summary = run_eval(
        dataset=REPO_DATA,
        provider=MockProvider(pass_rate_pct=100),
        output_json=out,
        output_md=md,
        output_html=html,
        cache_dir=cache,
        resume=False,
    )
    assert out.is_file()
    assert md.is_file()
    assert html.is_file()
    assert summary.is_mock
    assert summary.total == 150
    assert summary.passed == 150
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["is_mock"] is True
    md_text = md.read_text(encoding="utf-8").lower()
    assert "mock" in md_text


def test_run_eval_resumes(tmp_path: Path) -> None:
    out = tmp_path / "results.json"
    provider = MockProvider(pass_rate_pct=50)
    first = run_eval(
        dataset=REPO_DATA,
        provider=provider,
        output_json=out,
        resume=False,
        cache_dir=tmp_path / "cache1",
    )
    # Truncate to simulate partial run
    partial = json.loads(out.read_text(encoding="utf-8"))
    partial["items"] = partial["items"][:10]
    out.write_text(json.dumps(partial), encoding="utf-8")

    second = run_eval(
        dataset=REPO_DATA,
        provider=provider,
        output_json=out,
        resume=True,
        cache_dir=tmp_path / "cache2",
    )
    assert second.total == 150
    assert len(second.items) == 150
    # First 10 should match the truncated run's pass flags
    for a, b in zip(first.items[:10], second.items[:10], strict=True):
        assert a.id == b.id
        assert a.passed == b.passed


def test_retries_eventually_fail(tmp_path: Path) -> None:
    class Boom(MockProvider):
        def complete(self, item: Item) -> ProviderResponse:
            raise ProviderError("nope")

    with pytest.raises(ProviderError):
        run_eval(
            dataset=REPO_DATA,
            provider=Boom(),
            output_json=tmp_path / "r.json",
            resume=False,
            retries=1,
            backoff_s=0.01,
            cache_dir=None,
        )


def test_cli_run_mock(tmp_path: Path) -> None:
    out = tmp_path / "out.json"
    result = runner.invoke(
        app,
        [
            "run",
            "--dataset",
            str(REPO_DATA),
            "--output",
            str(out),
            "--md",
            str(tmp_path / "out.md"),
            "--html",
            str(tmp_path / "out.html"),
            "--cache-dir",
            str(tmp_path / "cache"),
            "--no-resume",
            "--mock-pass-rate",
            "100",
        ],
    )
    assert result.exit_code == 0, result.output
    assert out.is_file()
    assert "150" in result.output
