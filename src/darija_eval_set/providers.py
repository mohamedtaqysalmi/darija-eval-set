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
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass

from darija_eval_set.schema import Item


class ProviderError(RuntimeError):
    """Raised when a provider call fails.

    ``retryable`` is False for failures a retry cannot fix, such as a 401 or a malformed request.
    """

    def __init__(self, message: str, *, retryable: bool = True) -> None:
        super().__init__(message)
        self.retryable = retryable


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    model: str
    provider: str


class Provider(ABC):
    name: str
    # Whether responses may be stored in the disk cache. The mock derives its answer from the
    # item id and pass rate, not just the prompt, so it must not share cache entries.
    cacheable: bool = True

    @abstractmethod
    def complete(self, item: Item, *, system: str | None = None) -> ProviderResponse:
        """Return a model answer for one item, optionally with a custom system message."""


class MockProvider(Provider):
    """Deterministic offline provider. Correct on a stable subset of item ids."""

    name = "mock"
    model = "mock-v1"
    cacheable = False

    def __init__(self, *, pass_rate_pct: int = 70) -> None:
        if not 0 <= pass_rate_pct <= 100:
            raise ValueError("pass_rate_pct must be between 0 and 100")
        self.pass_rate_pct = pass_rate_pct

    def _should_pass(self, item_id: str) -> bool:
        digest = hashlib.sha256(item_id.encode("utf-8")).hexdigest()
        bucket = int(digest[:8], 16) % 100
        return bucket < self.pass_rate_pct

    def complete(self, item: Item, *, system: str | None = None) -> ProviderResponse:
        text = item.expected[0] if self._should_pass(item.id) else "MOCK_WRONG_ANSWER"
        return ProviderResponse(text=text, model=self.model, provider=self.name)


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
        _check_base_url(base_url)
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s

    def complete(self, item: Item, *, system: str | None = None) -> ProviderResponse:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system or _ANSWER_SYSTEM_PROMPT,
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
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            # 429 and 5xx can clear up on their own; other 4xx (bad key, bad request) cannot.
            retryable = exc.code == 429 or exc.code >= 500
            raise ProviderError(f"HTTP {exc.code}: {detail}", retryable=retryable) from exc
        except urllib.error.URLError as exc:
            raise ProviderError(str(exc.reason)) from exc
        except (TimeoutError, ConnectionError) as exc:
            raise ProviderError(f"{type(exc).__name__}: {exc}") from exc
        except ValueError as exc:
            raise ProviderError(f"response is not valid JSON: {exc}") from exc

        try:
            text = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"unexpected response shape: {str(body)[:200]!r}") from exc
        if not isinstance(text, str):
            raise ProviderError("message content is not a string", retryable=False)
        return ProviderResponse(text=text, model=self.model, provider=self.name)


_ANSWER_SYSTEM_PROMPT = (
    "You answer Moroccan Darija evaluation prompts. "
    "Follow the user instructions exactly. "
    "Reply with only the answer text, no preface."
)

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _check_base_url(base_url: str) -> None:
    """Allow https, and plain http only for a local server.

    urllib would otherwise open file:// URLs, and plain http would send the API key in clear text.
    """
    parsed = urllib.parse.urlparse(base_url)
    if parsed.scheme == "https" and parsed.hostname:
        return
    if parsed.scheme == "http" and parsed.hostname in _LOCAL_HOSTS:
        return
    raise ValueError(
        "DARIJA_EVAL_BASE_URL must be an https URL (http is allowed for localhost only), "
        f"got {base_url!r}"
    )


def provider_from_env() -> Provider:
    kind = os.environ.get("DARIJA_EVAL_PROVIDER", "mock").strip().lower()
    if kind == "mock":
        return MockProvider()
    if kind == "openai_compat":
        return OpenAICompatProvider(
            api_key=os.environ.get("DARIJA_EVAL_API_KEY", ""),
            base_url=os.environ.get("DARIJA_EVAL_BASE_URL")
            or "https://api.openai.com/v1/chat/completions",
            model=os.environ.get("DARIJA_EVAL_MODEL") or "gpt-4o-mini",
        )
    raise ValueError(f"unknown DARIJA_EVAL_PROVIDER {kind!r}; expected 'mock' or 'openai_compat'")
