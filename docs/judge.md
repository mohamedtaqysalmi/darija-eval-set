# LLM judge (optional)

See [judge-prompt.md](judge-prompt.md) for the full system/user prompts.

Summary:

- Off by default (`--no-judge`)
- Never downgrades a rule-based pass
- Mock provider: accept iff candidate equals an expected string after strip
- Live provider: YES/NO chat completion via the same OpenAI-compatible client
