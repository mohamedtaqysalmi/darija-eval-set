"""Serialize run results to JSON, Markdown and HTML tables."""

from __future__ import annotations

import html
import json
import os
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class ItemResult:
    id: str
    category: str
    scoring: str
    passed: bool
    prediction: str
    expected: list[str]
    cached: bool
    judge_used: bool = False


@dataclass
class RunSummary:
    generated_at: str
    provider: str
    model: str
    dataset: str
    is_mock: bool
    total: int
    passed: int
    failed: int
    accuracy: float
    by_category: dict[str, dict[str, float | int]]
    items: list[ItemResult]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


def build_summary(
    *,
    provider: str,
    model: str,
    dataset: str,
    is_mock: bool,
    items: list[ItemResult],
) -> RunSummary:
    passed = sum(1 for i in items if i.passed)
    total = len(items)
    by_cat: dict[str, dict[str, float | int]] = {}
    counts: Counter[str] = Counter(i.category for i in items)
    pass_counts: Counter[str] = Counter(i.category for i in items if i.passed)
    for category, n in sorted(counts.items()):
        p = pass_counts[category]
        by_cat[category] = {
            "total": n,
            "passed": p,
            "accuracy": round(p / n, 4) if n else 0.0,
        }
    return RunSummary(
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        provider=provider,
        model=model,
        dataset=dataset,
        is_mock=is_mock,
        total=total,
        passed=passed,
        failed=total - passed,
        accuracy=round(passed / total, 4) if total else 0.0,
        by_category=by_cat,
        items=items,
    )


def write_json(summary: RunSummary, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write to a temp file first so a kill mid-write cannot leave a truncated results.json
    # that breaks the next resume.
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(
        json.dumps(summary.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, path)


def render_markdown(summary: RunSummary) -> str:
    mock_note = " **MOCK run — not a real model score.**" if summary.is_mock else ""
    lines = [
        f"# Darija eval results{mock_note}",
        "",
        f"- Generated: `{summary.generated_at}`",
        f"- Provider / model: `{summary.provider}` / `{summary.model}`",
        f"- Dataset: `{summary.dataset}`",
        f"- Overall: **{summary.passed}/{summary.total}** ({summary.accuracy:.1%})",
        "",
        "## By category",
        "",
        "| Category | Passed | Total | Accuracy |",
        "| --- | ---: | ---: | ---: |",
    ]
    for category, stats in summary.by_category.items():
        lines.append(
            f"| {category} | {stats['passed']} | {stats['total']} | "
            f"{float(stats['accuracy']):.1%} |"
        )
    lines.extend(
        [
            "",
            "## Items",
            "",
            "| ID | Category | Pass | Cached | Judge |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in summary.items:
        lines.append(
            f"| {row.id} | {row.category} | {'yes' if row.passed else 'no'} | "
            f"{'yes' if row.cached else 'no'} | {'yes' if row.judge_used else 'no'} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_html(summary: RunSummary) -> str:
    mock_banner = (
        (
            '<p class="mock">MOCK run — numbers come from the offline mock provider, '
            "not a live model.</p>"
        )
        if summary.is_mock
        else ""
    )
    esc = html.escape
    cat_rows = "".join(
        f"<tr><td>{esc(cat)}</td><td>{s['passed']}</td><td>{s['total']}</td>"
        f"<td>{float(s['accuracy']):.1%}</td></tr>"
        for cat, s in summary.by_category.items()
    )
    item_rows = "".join(
        f"<tr><td>{esc(r.id)}</td><td>{esc(r.category)}</td>"
        f"<td>{'yes' if r.passed else 'no'}</td>"
        f"<td>{'yes' if r.cached else 'no'}</td>"
        f"<td>{'yes' if r.judge_used else 'no'}</td></tr>"
        for r in summary.items
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Darija eval results</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #14201c; }}
    .mock {{ background: #fff3cd; padding: .75rem 1rem; border-left: 4px solid #c77700; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #c5d0cb; padding: .4rem .6rem; text-align: left; }}
    th {{ background: #e7efeb; }}
  </style>
</head>
<body>
  <h1>Darija eval results</h1>
  {mock_banner}
  <ul>
    <li>Generated: <code>{esc(summary.generated_at)}</code></li>
    <li>Provider / model: <code>{esc(summary.provider)}</code> /
      <code>{esc(summary.model)}</code></li>
    <li>Dataset: <code>{esc(summary.dataset)}</code></li>
    <li>Overall: <strong>{summary.passed}/{summary.total}</strong> ({summary.accuracy:.1%})</li>
  </ul>
  <h2>By category</h2>
  <table>
    <thead><tr><th>Category</th><th>Passed</th><th>Total</th><th>Accuracy</th></tr></thead>
    <tbody>{cat_rows}</tbody>
  </table>
  <h2>Items</h2>
  <table>
    <thead><tr><th>ID</th><th>Category</th><th>Pass</th><th>Cached</th><th>Judge</th></tr></thead>
    <tbody>{item_rows}</tbody>
  </table>
</body>
</html>
"""


def write_tables(summary: RunSummary, md_path: Path | None, html_path: Path | None) -> None:
    if md_path is not None:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_markdown(summary), encoding="utf-8")
    if html_path is not None:
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(render_html(summary), encoding="utf-8")


def load_existing_item_results(
    path: Path, *, provider: str, model: str, dataset: str
) -> dict[str, ItemResult]:
    """Load prior item rows from a results.json for resume.

    Rows are only reused when the earlier run used the same provider, model and dataset path;
    otherwise the new run would silently mix results from different models.
    """
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        same_run = (
            data["provider"] == provider and data["model"] == model and data["dataset"] == dataset
        )
        if not same_run:
            return {}
        out: dict[str, ItemResult] = {}
        for raw in data["items"]:
            out[raw["id"]] = ItemResult(
                id=raw["id"],
                category=raw["category"],
                scoring=raw["scoring"],
                passed=bool(raw["passed"]),
                prediction=raw["prediction"],
                expected=list(raw["expected"]),
                cached=bool(raw.get("cached", False)),
                judge_used=bool(raw.get("judge_used", False)),
            )
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError(
            f"{path} cannot be used to resume ({type(exc).__name__}: {exc}); "
            "fix or delete it, or pass --no-resume"
        ) from exc
    return out
