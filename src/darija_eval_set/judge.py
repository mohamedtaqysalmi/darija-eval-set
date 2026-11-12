"""Optional LLM-as-judge scoring (behind a CLI flag).

The judge is off by default. When enabled, it can only override a miss from
rule-based scoring; a rule-based hit stays a hit. The prompt is documented in
``docs/judge-prompt.md``.
"""

from __future__ import annotations

from darija_eval_set.providers import MockProvider, Provider, ProviderResponse
from darija_eval_set.schema import Item, ScoringMethod

JUDGE_SYSTEM_PROMPT = (
    "You are a careful bilingual evaluator for Moroccan Darija benchmarks. "
    "Decide if the candidate answer is semantically acceptable for the prompt "
    "given the listed expected answers. Reply with exactly YES or NO."
)


def build_judge_user_prompt(item: Item, prediction: str) -> str:
    expected = "\n".join(f"- {e}" for e in item.expected)
    return (
        f"Prompt:\n{item.prompt}\n\n"
        f"Expected answers (any one may be enough):\n{expected}\n\n"
        f"Candidate:\n{prediction}\n\n"
        "Is the candidate acceptable? Reply YES or NO."
    )


class Judge:
    """Wraps a provider used only for yes/no judging."""

    def __init__(self, provider: Provider) -> None:
        self.provider = provider

    def accepts(self, item: Item, prediction: str) -> bool:
        # Mock judge: accept when the prediction equals any expected after strip,
        # else reject. Keeps offline runs deterministic without calling a model.
        if isinstance(self.provider, MockProvider):
            return any(prediction.strip() == e.strip() for e in item.expected)

        prompt_item = Item(
            id=item.id,
            category=item.category,
            prompt=build_judge_user_prompt(item, prediction),
            expected=["YES"],
            scoring=ScoringMethod.NORMALIZED,
            threshold=None,
            languages=item.languages,
            notes=item.notes,
            review_status=item.review_status,
        )
        # Reuse the provider transport with a synthetic prompt.
        response: ProviderResponse = self.provider.complete(prompt_item, system=JUDGE_SYSTEM_PROMPT)
        answer = response.text.strip().upper()
        return answer.startswith("YES")
