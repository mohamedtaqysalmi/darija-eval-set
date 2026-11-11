# Contributing

This project is maintained by one person. Issues and pull requests are welcome, but replies may take a few days.

## Setup

You need Python 3.11 or newer.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows; on macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Checks

CI runs the same commands on Python 3.11 and 3.14. Run them before pushing:

```bash
ruff check .
ruff format --check .
mypy
pytest
python -m build
```

Coverage must stay at or above 85%.

## Branches and commits

Branch from `main` and name the branch `type/short-description`, for example `feat/jsonl-schema` or `fix/scoring-rounding`. Use the same types as Conventional Commits: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`.

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/). Pull requests are squash-merged, so the PR title becomes the commit message on `main` and should follow the same format.

## Pull requests

- Keep a PR to one change. Open an issue first if it is large or changes the dataset schema.
- Fill in the PR template: what, why, how you tested it.
- Add or update tests for behavior changes, and update `CHANGELOG.md` under Unreleased.
- CI has to be green before merge.

## Dataset contributions

Prompts and expected answers should be written by you, or come from a source whose license allows redistribution under this project's terms. Say where an item came from in the PR. Do not include personal data.

By contributing you agree that your contribution is licensed under the MIT license.

## Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
