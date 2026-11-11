# darija-eval-set

An open benchmark of Moroccan Darija prompts with expected answers, plus a command-line runner that scores any model or API against them.

Status: early. There is an item schema, 18 seed items in `data/items.jsonl`, a `validate` command and scoring functions. The items are drafts and have not been reviewed by a native speaker yet, so they do not count as a benchmark. There is no runner or provider support yet, so nothing can be scored against a model.

## Dataset

`data/items.jsonl` has one JSON object per line: `id`, `category`, `prompt`, `expected` (list of accepted answers), `scoring` (`exact`, `normalized` or `fuzzy`), `threshold` (fuzzy only), `languages`, `notes` and `review_status` (`draft`, `reviewed` or `rejected`). Categories are translation, qa, sentiment, code_switching, instruction_following and safety_refusal, three seed items each. Every item is currently `draft`.

## Validating the data

```bash
darija-eval validate                  # checks data/items.jsonl
darija-eval validate path/to/file.jsonl
```

It prints `file:line: reason` for every bad line and exits with status 1 if there are any. CI runs it on `data/items.jsonl`.

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
