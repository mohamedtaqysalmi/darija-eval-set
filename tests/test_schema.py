from typing import Any

import pytest
from pydantic import ValidationError

from darija_eval_set.schema import Item


def make(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "qa-001",
        "category": "qa",
        "prompt": "شنو هي عاصمة المغرب؟",
        "expected": ["الرباط"],
        "scoring": "normalized",
        "languages": ["ary"],
        "review_status": "draft",
    }
    return base | overrides


def test_valid_item_parses() -> None:
    item = Item.model_validate(make())
    assert item.notes is None
    assert item.threshold is None


@pytest.mark.parametrize(
    "overrides",
    [
        {"category": "poetry"},
        {"prompt": "   "},
        {"expected": []},
        {"expected": [""]},
        {"languages": []},
        {"review_status": "approved"},
        {"id": "qa_001"},
        {"id": "translation-001"},
        {"extra_field": 1},
        {"scoring": "fuzzy"},
        {"threshold": 0.8},
        {"scoring": "fuzzy", "threshold": 1.5},
    ],
)
def test_malformed_item_is_rejected(overrides: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        Item.model_validate(make(**overrides))


def test_fuzzy_with_threshold_is_valid() -> None:
    item = Item.model_validate(make(scoring="fuzzy", threshold=0.8))
    assert item.threshold == 0.8
