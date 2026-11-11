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
darija-eval validate
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

1. Prefer the [Propose new items](https://github.com/mohamedtaqysalmi/darija-eval-set/issues/new?template=propose_items.yml) issue template before a large PR.
2. Write prompts and expected answers yourself, or cite a license that allows MIT redistribution.
3. No personal data, no copyrighted quotes, no actionable harmful instructions.
4. New lines must pass `darija-eval validate`. Keep `review_status` as `draft` unless you are the designated reviewer.
5. Matching id prefix and category (`qa-027` with `"category": "qa"`).
6. Update `DATASHEET.md` if the item count or review mix changes.

### Review checklist (maintainers)

- [ ] Schema valid, unique ids
- [ ] Expected answers short and scorable with the declared method
- [ ] Fuzzy items have a sensible `threshold`
- [ ] Safety items stay on the fixed refusal template
- [ ] Notes mention ambiguity when needed

## Submitting model results

Run with a real provider, keep the raw `results.json`, and open a PR that documents provider, model, date, and command. Prefer adding `site/runs/<name>.json` so the mock baseline in `site/results.json` stays.

## Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
