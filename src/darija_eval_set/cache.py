"""Disk cache for provider responses."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from darija_eval_set.providers import ProviderResponse


def cache_key(provider: str, model: str, prompt: str) -> str:
    raw = f"{provider}\0{model}\0{prompt}".encode()
    return hashlib.sha256(raw).hexdigest()


class ResponseCache:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.root / f"{key}.json"

    def get(self, key: str) -> ProviderResponse | None:
        path = self._path(key)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return ProviderResponse(
                text=data["text"],
                model=data["model"],
                provider=data["provider"],
            )
        except (ValueError, KeyError, TypeError):
            # A truncated or hand-edited entry is treated as a miss and overwritten.
            return None

    def set(self, key: str, response: ProviderResponse) -> None:
        path = self._path(key)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(
                {
                    "text": response.text,
                    "model": response.model,
                    "provider": response.provider,
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        tmp.replace(path)
