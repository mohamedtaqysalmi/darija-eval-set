# QA notes (v0.1.0)

Manual and automated checks before tagging. Automated results live in [TEST_REPORT.md](TEST_REPORT.md).

## Scope

In scope: 150-item JSONL, Pydantic validate, Typer runner (mock + openai_compat env), cache/resume/retries, results tables, static Pages leaderboard, datasheet, CI.

Out of scope for this tag: PyPI publish, native-speaker item review, live paid-API leaderboard, demo GIF.

## Automated gate (must be green)

| Check | Command / place |
| --- | --- |
| Lint | `ruff check .` |
| Format | `ruff format --check .` |
| Types | `mypy` |
| Validate dataset | `darija-eval validate data/items.jsonl` |
| Tests + coverage ≥ 85% | `pytest` |
| Wheel build | `python -m build` (CI) |
| CI matrix | Python 3.11 and 3.14 on `ubuntu-latest` |

## Manual checklist (human)

- [ ] Open https://mohamedtaqysalmi.github.io/darija-eval-set/ after Pages deploy
- [ ] Mock banner visible; overall counts match `site/results.json`
- [ ] Category chips filter the item table
- [ ] Copy quickstart button works in Chromium
- [ ] Light / dark OS theme: text readable on hero and tables
- [ ] Mobile ~375px: brand and leaderboard usable, no horizontal page scroll
- [ ] `darija-eval run --mock-pass-rate 100` finishes and labels MOCK
- [ ] DATASHEET.md item count matches JSONL

## Honesty checks

- README and site say items are unreviewed drafts
- Pages numbers labelled mock when `is_mock` is true
- No copyrighted prompts in `data/items.jsonl`
- No Co-Authored-By / AI attribution in commits or PR bodies

## Sign-off

Automated gate: see TEST_REPORT.md for the local run used at tag time. CI on `main` after squash-merge is the public record.
