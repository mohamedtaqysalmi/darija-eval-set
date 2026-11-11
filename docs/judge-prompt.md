# LLM-as-judge prompt

The `--judge` flag is **off by default**. When on, rule-based scoring still runs first. The judge only sees items that already failed exact / normalized / fuzzy match. A rule-based pass is never downgraded.

## System message

```
You are a careful bilingual evaluator for Moroccan Darija benchmarks.
Decide if the candidate answer is semantically acceptable for the prompt
given the listed expected answers. Reply with exactly YES or NO.
```

## User message template

```
Prompt:
{item.prompt}

Expected answers (any one may be enough):
- {expected_1}
- {expected_2}
...

Candidate:
{prediction}

Is the candidate acceptable? Reply YES or NO.
```

## Offline behaviour

With the mock provider, the judge accepts only when the candidate equals an expected string after strip. That keeps CI deterministic. Live OpenAI-compatible providers receive the prompts above through the same chat-completions client.

## Honesty

Do not publish judge-boosted numbers next to rule-only numbers without saying so. The shipped `site/results.json` is a **mock** rule-only run.
