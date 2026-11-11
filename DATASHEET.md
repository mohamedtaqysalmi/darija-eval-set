# Dataset card — darija-eval-set

## Motivation

I needed a small, public Moroccan Darija eval set I can run offline against any chat API. Most Arabic benchmarks are Modern Standard Arabic; Darija chat text mixes Arabic script, French loans and English tech words. This dataset is a starting point, not a finished gold standard.

## Composition

| Field | Value |
| --- | --- |
| File | `data/items.jsonl` |
| Size | 150 items (25 per category) |
| Categories | translation, qa, sentiment, code_switching, instruction_following, safety_refusal |
| Languages tagged | `ary` (Darija), plus `fr`, `en`, `ar` where relevant |
| Review status | all `draft` until a native-speaker pass |
| License | MIT (same as the repo) |

Each line is one JSON object validated by the Pydantic `Item` schema in CI.

## How items were made

I wrote the prompts and expected answers myself for this repository. Nothing was copied from copyrighted exams, books, news articles or commercial datasets. Safety items use a fixed refusal template (`غادي نعاونك` / `ما نقدرش نعاونك`) so scoring stays mechanical; the underlying requests are mild, obviously refusable scenarios.

Expected answers are short. Translation and code-switching items often list more than one acceptable string and use fuzzy scoring with an explicit threshold.

## Who reviewed

Nobody outside the author has reviewed the items yet. Treat accuracy of Darija wording as provisional. The `review_status` field exists so a later pass can mark `reviewed` or `rejected` without changing the schema.

## Scoring notes

| Method | Use |
| --- | --- |
| `exact` | Byte-for-byte match (instruction following) |
| `normalized` | Case, whitespace, punctuation, Arabic diacritics, alef/ya variants |
| `fuzzy` | Normalized difflib ratio ≥ `threshold` |

Optional LLM-as-judge is behind `--judge` and is documented in `docs/judge-prompt.md`. It is off in the shipped mock results.

## Intended uses

- Offline smoke tests of Darija-capable models via the mock or an OpenAI-compatible provider
- CI validation of JSONL contributions
- A public leaderboard page fed by `results.json` from runs you actually execute

## Not intended uses

- Claiming a production Darija leaderboard without native-speaker review
- Training a commercial model on the items as if they were curated gold data
- Evaluating harmful capability beyond the mild refusal template (do not expand safety prompts into actionable instructions)

## Known biases and gaps

- Author is one person in Morocco; regional Darija variants (north/south, Arabizi-heavy chat) are under-represented
- Sentiment labels are three-way only; sarcasm is absent
- QA items favour factual, short answers; open-ended dialogue is out of scope
- French/English code-switching leans toward office and city vocabulary
- All items are currently drafts

## Maintenance

Propose new items via the “Propose new items” issue template. PRs that touch `data/items.jsonl` must keep `darija-eval validate` green. Update this card when the review status mix or item count changes.
