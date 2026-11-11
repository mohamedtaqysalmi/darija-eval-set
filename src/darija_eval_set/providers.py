"""Model providers used by the runner.

Configure with environment variables:

- ``DARIJA_EVAL_PROVIDER``: ``mock`` (default) or ``openai_compat``
- ``DARIJA_EVAL_API_KEY``: required for ``openai_compat``
- ``DARIJA_EVAL_BASE_URL``: OpenAI-compatible chat completions URL
  (default ``https://api.openai.com/v1/chat/completions``)
- ``DARIJA_EVAL_MODEL``: model name sent to the API (default ``gpt-4o-mini``)
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass

from darija_eval_set.schema import Item


class ProviderError(RuntimeError):
    """Raised when a provider call fails after the transport layer returns an error."""


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    model: str
    provider: str


class Provider(ABC):
    name: str

    @abstractmethod
    def complete(self, item: Item) -> ProviderResponse:
        """Return a model answer for one item."""


class MockProvider(Provider):
    """Deterministic offline provider. Correct on a stable subset of item ids."""

    name = "mock"

    def __init__(self, *, pass_rate_pct: int = 70) -> None:
        if not 0 <= pass_rate_pct <= 100:
            raise ValueError("pass_rate_pct must be between 0 and 100")
        self.pass_rate_pct = pass_rate_pct

    def _should_pass(self, item_id: str) -> bool:
        digest = hashlib.sha256(item_id.encode("utf-8")).hexdigest()
        bucket = int(digest[:8], 16) % 100
        return bucket < self.pass_rate_pct

    def complete(self, item: Item) -> ProviderResponse:
        text = item.expected[0] if self._should_pass(item.id) else "MOCK_WRONG_ANSWER"
        return ProviderResponse(text=text, model="mock-v1", provider=self.name)


class OpenAICompatProvider(Provider):
    """Minimal OpenAI-compatible chat completions client using stdlib urllib."""

    name = "openai_compat"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout_s: float = 60.0,
    ) -> None:
        if not api_key:
            raise ValueError("DARIJA_EVAL_API_KEY is required for openai_compat")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s

    def complete(self, item: Item) -> ProviderResponse:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You answer Moroccan Darija evaluation prompts. "
                        "Follow the user instructions exactly. "
                        "Reply with only the answer text, no preface."
                    ),
                },
                {"role": "user", "content": item.prompt},
            ],
            "temperature": 0,
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ProviderError(f"HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise ProviderError(str(exc.reason)) from exc

        try:
            text = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"unexpected response shape: {body!r}") from exc
        if not isinstance(text, str):
            raise ProviderError("message content is not a string")
        return ProviderResponse(text=text, model=self.model, provider=self.name)


def provider_from_env() -> Provider:
    kind = os.environ.get("DARIJA_EVAL_PROVIDER", "mock").strip().lower()
    if kind == "mock":
        return MockProvider()
    if kind == "openai_compat":
        return OpenAICompatProvider(
            api_key=os.environ.get("DARIJA_EVAL_API_KEY", ""),
            base_url=os.environ.get(
                "DARIJA_EVAL_BASE_URL",
                "https://api.openai.com/v1/chat/completions",
            ),
            model=os.environ.get("DARIJA_EVAL_MODEL", "gpt-4o-mini"),
        )
    raise ValueError(f"unknown DARIJA_EVAL_PROVIDER {kind!r}; expected 'mock' or 'openai_compat'")
