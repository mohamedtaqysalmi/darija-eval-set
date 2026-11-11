# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Project scaffold: packaging, lint, type-check and test configuration.
- Pydantic item schema with six categories and a `review_status` field.
- 18 draft seed items in `data/items.jsonl`, three per category, pending native-speaker review.
- `darija-eval validate` command reporting file, line and reason for each invalid line.
- Scoring functions: exact, normalized (case, whitespace, punctuation, Arabic diacritics, alef and ya variants) and fuzzy ratio with a threshold.
