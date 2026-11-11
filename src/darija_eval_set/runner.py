"""Eval runner: retries, cache, resume, scoring."""

from __future__ import annotations

import time
from pathlib import Path

from darija_eval_set.cache import ResponseCache, cache_key
from darija_eval_set.dataset import load_items
from darija_eval_set.judge import Judge
from darija_eval_set.providers import Provider, ProviderError, ProviderResponse
from darija_eval_set.results import (
    ItemResult,
    RunSummary,
    build_summary,
    load_existing_item_results,
    render_markdown,
    write_json,
    write_tables,
)
from darija_eval_set.schema import Item
from darija_eval_set.scoring import score


def _call_with_retries(
    provider: Provider,
    item: Item,
    *,
    retries: int,
    backoff_s: float,
) -> ProviderResponse:
    attempt = 0
    while True:
        try:
            return provider.complete(item)
        except ProviderError:
            if attempt >= retries:
                raise
            time.sleep(backoff_s * (2**attempt))
            attempt += 1


def run_eval(
    *,
    dataset: Path,
    provider: Provider,
    output_json: Path,
    output_md: Path | None = None,
    output_html: Path | None = None,
    cache_dir: Path | None = None,
    resume: bool = True,
    retries: int = 2,
    backoff_s: float = 0.5,
    use_judge: bool = False,
    judge: Judge | None = None,
) -> RunSummary:
    items, errors = load_items(dataset)
    if errors:
        raise ValueError(f"dataset has {len(errors)} invalid line(s); fix before running")

    cache = ResponseCache(cache_dir) if cache_dir is not None else None
    prior = load_existing_item_results(output_json) if resume else {}
    results: list[ItemResult] = []
    model_name = getattr(provider, "model", provider.name)

    for item in items:
        if item.id in prior:
            results.append(prior[item.id])
            continue

        cached = False
        model_for_key = getattr(provider, "model", provider.name)
        key = cache_key(provider.name, model_for_key, item.prompt)
        response: ProviderResponse | None = cache.get(key) if cache else None
        if response is not None:
            cached = True
        else:
            response = _call_with_retries(provider, item, retries=retries, backoff_s=backoff_s)
            if cache is not None:
                cache.set(key, response)

        model_name = response.model
        passed = score(item.scoring, response.text, item.expected, item.threshold)
        judge_used = False
        if not passed and use_judge and judge is not None:
            judge_used = True
            if judge.accepts(item, response.text):
                passed = True

        results.append(
            ItemResult(
                id=item.id,
                category=item.category.value,
                scoring=item.scoring.value,
                passed=passed,
                prediction=response.text,
                expected=list(item.expected),
                cached=cached,
                judge_used=judge_used,
            )
        )
        # Checkpoint after each new item so interrupted runs can resume.
        write_json(
            build_summary(
                provider=provider.name,
                model=model_name,
                dataset=str(dataset).replace("\\", "/"),
                is_mock=provider.name == "mock",
                items=results,
            ),
            output_json,
        )

    summary = build_summary(
        provider=provider.name,
        model=model_name,
        dataset=str(dataset).replace("\\", "/"),
        is_mock=provider.name == "mock",
        items=results,
    )
    write_json(summary, output_json)
    if output_md is not None and output_html is not None:
        write_tables(summary, output_md, output_html)
    elif output_md is not None:
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(render_markdown(summary), encoding="utf-8")
    return summary
