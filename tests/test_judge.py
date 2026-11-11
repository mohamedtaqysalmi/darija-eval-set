from darija_eval_set.judge import JUDGE_SYSTEM_PROMPT, Judge, build_judge_user_prompt
from darija_eval_set.providers import MockProvider
from darija_eval_set.schema import Item


def _item() -> Item:
    return Item.model_validate(
        {
            "id": "qa-001",
            "category": "qa",
            "prompt": "عاصمة؟",
            "expected": ["الرباط"],
            "scoring": "normalized",
            "languages": ["ary"],
            "review_status": "draft",
        }
    )


def test_build_judge_user_prompt_includes_parts() -> None:
    text = build_judge_user_prompt(_item(), "الرباط")
    assert "عاصمة؟" in text
    assert "الرباط" in text
    assert "YES or NO" in text
    assert "careful bilingual" in JUDGE_SYSTEM_PROMPT


def test_mock_judge_accepts_exact_expected() -> None:
    judge = Judge(MockProvider(pass_rate_pct=100))
    assert judge.accepts(_item(), "الرباط") is True
    assert judge.accepts(_item(), "wrong") is False
