# CLI reference

Entry point: `darija-eval` (module `darija_eval_set.cli`).

## `darija-eval validate [path]`

Validate a JSONL items file against the Pydantic schema.

- Default path: `data/items.jsonl`
- Prints `file:line: reason` for each error
- Exit `1` if any line is invalid; exit `2` if the file is missing

## `darija-eval run`

Score every item with a provider and write results.

| Option | Default | Meaning |
| --- | --- | --- |
| `--dataset` | `data/items.jsonl` | Dataset path |
| `--output` | `results/results.json` | JSON results path |
| `--md` | `results/results.md` | Markdown table |
| `--html` | `results/results.html` | HTML table |
| `--cache-dir` | `.cache/darija-eval` | Response cache directory |
| `--no-cache` | off | Disable disk cache |
| `--no-resume` | off | Ignore existing `results.json` |
| `--retries` | `2` | Retries on provider errors |
| `--judge` / `--no-judge` | `--no-judge` | Optional LLM judge on rule-based misses |
| `--mock-pass-rate` | provider default (70) | Mock-only pass bucket percent |

### Environment

| Variable | Default | Meaning |
| --- | --- | --- |
| `DARIJA_EVAL_PROVIDER` | `mock` | `mock` or `openai_compat` |
| `DARIJA_EVAL_API_KEY` | empty | Required for `openai_compat` |
| `DARIJA_EVAL_BASE_URL` | OpenAI chat completions URL | OpenAI-compatible endpoint |
| `DARIJA_EVAL_MODEL` | `gpt-4o-mini` | Model name for live calls |

### LLM judge

`--judge` only runs after a rule-based miss. Prompt text: [judge-prompt.md](judge-prompt.md). With the mock provider the judge stays deterministic (exact expected match after strip).
