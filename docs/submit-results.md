# Submit model results

1. Run with a real provider:

```bash
set DARIJA_EVAL_PROVIDER=openai_compat
set DARIJA_EVAL_API_KEY=...
set DARIJA_EVAL_MODEL=your-model
darija-eval run --no-resume --output results/my-model.json
```

2. Confirm `is_mock` is `false` in the JSON.
3. Open a PR that either:
   - adds `site/runs/<model-slug>.json`, or
   - updates `site/submissions/index.json` to list the new file
4. In the PR body: provider, model, date, command, and whether `--judge` was used.

Keep `site/results.json` as the mock baseline unless maintainers agree to replace it.
