from collections import Counter
from pathlib import Path
from typing import Annotated

import typer

from darija_eval_set.dataset import load_items
from darija_eval_set.judge import Judge
from darija_eval_set.providers import MockProvider, ProviderError, provider_from_env
from darija_eval_set.runner import run_eval

app = typer.Typer(help="Tools for the darija-eval-set benchmark.", no_args_is_help=True)


@app.callback()
def main() -> None:
    """Tools for the darija-eval-set benchmark."""


@app.command()
def validate(
    path: Annotated[Path, typer.Argument(help="JSONL file to check.")] = Path("data/items.jsonl"),
) -> None:
    """Check every line of an items file against the schema."""
    if not path.is_file():
        typer.echo(f"{path}: file not found", err=True)
        raise typer.Exit(2)
    items, errors = load_items(path)
    for error in errors:
        typer.echo(str(error), err=True)
    if errors:
        typer.echo(f"{len(errors)} invalid line(s) in {path}", err=True)
        raise typer.Exit(1)
    counts = Counter(item.category.value for item in items)
    typer.echo(f"{path}: {len(items)} items OK")
    for category, n in sorted(counts.items()):
        typer.echo(f"  {category}: {n}")


@app.command("run")
def run_cmd(
    dataset: Annotated[Path, typer.Option("--dataset", help="JSONL items file.")] = Path(
        "data/items.jsonl"
    ),
    output: Annotated[Path, typer.Option("--output", help="results.json path.")] = Path(
        "results/results.json"
    ),
    md: Annotated[Path | None, typer.Option("--md", help="Markdown table path.")] = Path(
        "results/results.md"
    ),
    html: Annotated[Path | None, typer.Option("--html", help="HTML table path.")] = Path(
        "results/results.html"
    ),
    cache_dir: Annotated[
        Path | None,
        typer.Option(
            "--cache-dir",
            help="Response cache directory (live providers only; --no-cache disables).",
        ),
    ] = Path(".cache/darija-eval"),
    no_cache: Annotated[bool, typer.Option("--no-cache", help="Disable disk cache.")] = False,
    no_resume: Annotated[
        bool, typer.Option("--no-resume", help="Ignore existing results.json.")
    ] = False,
    retries: Annotated[int, typer.Option("--retries", min=0, help="Provider retries.")] = 2,
    judge: Annotated[
        bool,
        typer.Option(
            "--judge/--no-judge",
            help="Optional LLM-judge on rule-based misses (see docs/judge-prompt.md).",
        ),
    ] = False,
    mock_pass_rate: Annotated[
        int | None,
        typer.Option(
            "--mock-pass-rate",
            min=0,
            max=100,
            help="Only for mock provider: target pass bucket percent.",
        ),
    ] = None,
) -> None:
    """Score every item with the configured provider (mock by default)."""
    if not dataset.is_file():
        typer.echo(f"{dataset}: file not found", err=True)
        raise typer.Exit(2)

    try:
        provider = provider_from_env()
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc

    if mock_pass_rate is not None:
        if not isinstance(provider, MockProvider):
            typer.echo("--mock-pass-rate only applies to the mock provider", err=True)
            raise typer.Exit(2)
        provider = MockProvider(pass_rate_pct=mock_pass_rate)

    judge_obj = Judge(provider) if judge else None
    cache_path = None if no_cache else cache_dir

    try:
        summary = run_eval(
            dataset=dataset,
            provider=provider,
            output_json=output,
            output_md=md,
            output_html=html,
            cache_dir=cache_path,
            resume=not no_resume,
            retries=retries,
            use_judge=judge,
            judge=judge_obj,
        )
    except (ValueError, OSError, ProviderError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    label = "MOCK" if summary.is_mock else summary.provider
    typer.echo(
        f"{label}: {summary.passed}/{summary.total} passed ({summary.accuracy:.1%}) → {output}"
    )
    if summary.is_mock:
        typer.echo("Note: mock provider — not a live model score.", err=True)
