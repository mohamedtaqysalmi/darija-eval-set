import pytest

from darija_eval_set.schema import ScoringMethod
from darija_eval_set.scoring import (
    exact_match,
    fuzzy_match,
    fuzzy_ratio,
    normalize,
    normalized_match,
    score,
)


def test_exact_match_is_strict() -> None:
    assert exact_match("الرباط", ["الرباط"])
    assert not exact_match("الرباط ", ["الرباط"])
    assert not exact_match("rabat", ["Rabat"])
    assert not exact_match("", ["الرباط"])


def test_exact_match_any_of_several() -> None:
    assert exact_match("كازابلانكا", ["الدار البيضاء", "كازابلانكا"])


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  Hello,   WORLD! ", "hello world"),
        ("مَرْحَبًا", "مرحبا"),
        ("أحمد إبراهيم آمنة", "احمد ابراهيم امنة"),
        ("على", "علي"),
        ("كـــلمة", "كلمة"),
        ("شنو؟ واش، ايه!", "شنو واش ايه"),
        ("I'm here", "im here"),
        ("", ""),
    ],
)
def test_normalize(raw: str, expected: str) -> None:
    assert normalize(raw) == expected


def test_normalized_match_ignores_case_space_punctuation() -> None:
    assert normalized_match("  where is the NEAREST pharmacy ?", ["Where is the nearest pharmacy?"])


def test_normalized_match_arabic_variants() -> None:
    assert normalized_match("إيجابي.", ["ايجابي"])
    assert normalized_match("مُحَايِد", ["محايد"])
    assert normalized_match("مستشفى", ["مستشفي"])


def test_normalized_match_rejects_different_text() -> None:
    assert not normalized_match("سلبي", ["إيجابي"])


def test_normalized_match_empty_never_matches() -> None:
    assert not normalized_match("", ["الرباط"])
    assert not normalized_match("...", [""])
    assert not normalized_match("   ", [""])


def test_fuzzy_ratio_bounds() -> None:
    assert fuzzy_ratio("الرباط", ["الرباط"]) == 1.0
    assert fuzzy_ratio("abc", ["xyz"]) == 0.0
    assert fuzzy_ratio("", ["الرباط"]) == 0.0
    assert fuzzy_ratio("الرباط", []) == 0.0


def test_fuzzy_match_threshold() -> None:
    expected = ["I would like a glass of water, please."]
    assert fuzzy_match("I would like a glass of water please", expected, 0.9)
    assert not fuzzy_match("Where is the pharmacy?", expected, 0.9)


def test_fuzzy_match_arabic_script() -> None:
    assert fuzzy_match("غادي للسوق غدّا", ["غادي للسوق غدا"], 0.95)
    assert fuzzy_match("غادي للسوق", ["أنا غادي للسوق غدا"], 0.6)
    assert not fuzzy_match("", ["غادي للسوق غدا"], 0.1)


def test_score_dispatch() -> None:
    assert score(ScoringMethod.EXACT, "7", ["7"])
    assert not score(ScoringMethod.EXACT, "7.", ["7"])
    assert score(ScoringMethod.NORMALIZED, "7.", ["7"])
    assert score(ScoringMethod.FUZZY, "hello world", ["Hello, world"], 0.9)


def test_score_fuzzy_requires_threshold() -> None:
    with pytest.raises(ValueError, match="threshold"):
        score(ScoringMethod.FUZZY, "a", ["a"])
