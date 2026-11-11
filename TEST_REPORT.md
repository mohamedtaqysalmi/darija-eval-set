# Test report — v0.1.0

Local gate run on Windows before opening the MVP PR.

## Environment

- OS: Windows 10
- Python: 3.15.2 (local); CI matrix 3.11 and 3.14
- Package: editable install of `darija-eval-set==0.1.0`

## Commands

```text
ruff check src tests
ruff format --check src tests
mypy
darija-eval validate data/items.jsonl
pytest
darija-eval run --no-resume
```

## Results

| Check | Result |
| --- | --- |
| Ruff lint | pass |
| Ruff format | pass |
| Mypy (strict) | pass |
| Dataset validate | 150 items OK (25 × 6 categories) |
| Pytest | 59 passed, coverage 88.93% (fail_under 85) |
| Mock run | wrote `results/results.json` with `is_mock: true`; copied to `site/results.json` |

Public CI on the PR / `main` is the authoritative record after merge.
