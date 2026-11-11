from collections import Counter
from pathlib import Path
from typing import Annotated

import typer

from darija_eval_set.dataset import load_items

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
