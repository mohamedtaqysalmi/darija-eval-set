# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Rebuilt the Pages site on the shared style (`base.css`, `base.js`, `page.css`); web fonts, decoration and the old stylesheet are gone.
- Removed `site/results.html` and `site/results.md`, which duplicated the leaderboard with a different timestamp.

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
