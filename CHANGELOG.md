# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- The mock provider's answers were cached by prompt only, so `--mock-pass-rate` changes were silently ignored on a second run. The mock is no longer cached.
- Resume reused rows from any earlier `results.json`, even from another provider, model or dataset, or for items whose answers had changed. It now checks all of these, and an unreadable results file gives a clear error.
- The judge sent the answering system prompt instead of the documented judge prompt.
- `DARIJA_EVAL_BASE_URL` accepted `file://` and plain `http://` URLs. Only https, or http on localhost, is allowed now.
- Provider failures: 401 and other 4xx errors are no longer retried, timeouts and invalid JSON bodies become `ProviderError`, and `run` prints the error instead of a traceback.
- HTML results escape the model name and dataset path.
- `results.json` and cache files are written atomically; a corrupt cache entry counts as a miss.
- `validate` accepts a UTF-8 BOM and reports invalid UTF-8 instead of crashing.
- `--html` without `--md` wrote nothing.
- Removed `scripts/generate_items.py`: it no longer produced the shipped `data/items.jsonl` (130 of 150 items differed), so running it would have silently replaced the data.
- Docs and TEST_REPORT brought in line with the code.

## [0.1.0] — 2026-11-11

### Added

- 150 draft items in `data/items.jsonl` (25 per category) and `DATASHEET.md`.
- Typer `run` command with mock / OpenAI-compatible providers, retries, disk cache, resumable `results.json`.
- Results Markdown/HTML tables; optional `--judge` (see `docs/judge-prompt.md`).
- Static Pages leaderboard (`site/`) reading mock-labelled `results.json`.
- Architecture notes, QA checklist, propose-items issue template.

## [0.0.1] — 2026-11-11

### Added

- Project scaffold: packaging, lint, type-check and test configuration.
- Pydantic item schema with six categories and a `review_status` field.
- 18 draft seed items, `darija-eval validate`, and exact / normalized / fuzzy scoring.
