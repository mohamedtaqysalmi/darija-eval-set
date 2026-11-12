# Test report

Local gate run on the `fix/review-findings` branch. This is a snapshot, not a release record. CI on `main` is the authoritative result.

## Environment

- OS: Windows 11 (10.0.26300)
- Python: 3.15.2 (local); CI matrix 3.11 and 3.14
- Package: editable install of `darija-eval-set` 0.1.0

## Commands

```text
ruff check .
ruff format --check .
mypy
darija-eval validate
pytest
python -m build
darija-eval run --no-resume
```

## Results

| Check | Result |
| --- | --- |
| Ruff lint | pass |
| Ruff format | pass |
| Mypy (strict) | pass |
| Dataset validate | 150 items OK (25 per category, 6 categories) |
| Pytest | 84 passed, coverage 95.16% (`fail_under` is 85) |
| Build | sdist and wheel built |
| Mock run | 97/150 passed, `is_mock: true`; the same count as the shipped `site/results.json` |

## Not covered

- No test calls a real API. `OpenAICompatProvider` is tested with a patched `urlopen` only.
- The LLM judge is tested with the mock and with a stub provider, not against a live model.
- The Pages site was checked by hand in a browser, not by an automated test.
