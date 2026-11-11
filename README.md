# darija-eval-set

An open benchmark of Moroccan Darija prompts with expected answers, plus a command-line runner that scores any model or API against them.

Status: early scaffold, no dataset yet. There is no schema, runner or scoring code so far, only the project layout and tooling.

## Development setup

Requires Python 3.11 or newer.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows; on macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Running checks

```bash
pytest
ruff check .
ruff format --check .
mypy
```

`pytest` also reports coverage and fails below 85%.

## License

MIT, see [LICENSE](LICENSE).
