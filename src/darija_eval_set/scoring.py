import re
import unicodedata
from collections.abc import Iterable
from difflib import SequenceMatcher

from darija_eval_set.schema import ScoringMethod

# fathatan..sukun, superscript alef, and tatweel
_DIACRITICS = re.compile("[ً-ٰٟـ]")
_ALEF_VARIANTS = str.maketrans("أإآٱ", "اااا")
_YA_VARIANTS = str.maketrans("ى", "ي")
_APOSTROPHES = re.compile("['’ʼ]")
_SPACES = re.compile(r"\s+")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    text = _DIACRITICS.sub("", text)
    text = text.translate(_ALEF_VARIANTS).translate(_YA_VARIANTS)
    text = _APOSTROPHES.sub("", text)
    text = "".join(" " if unicodedata.category(c).startswith("P") else c for c in text)
    return _SPACES.sub(" ", text).strip()


def exact_match(prediction: str, expected: Iterable[str]) -> bool:
    return any(prediction == e for e in expected)


def normalized_match(prediction: str, expected: Iterable[str]) -> bool:
    pred = normalize(prediction)
    # a prediction that is only punctuation or whitespace never matches
    return bool(pred) and any(pred == normalize(e) for e in expected)


def fuzzy_ratio(prediction: str, expected: Iterable[str]) -> float:
    """Best difflib ratio between the normalized prediction and any expected answer."""
    pred = normalize(prediction)
    if not pred:
        return 0.0
    return max((SequenceMatcher(None, pred, normalize(e)).ratio() for e in expected), default=0.0)


def fuzzy_match(prediction: str, expected: Iterable[str], threshold: float) -> bool:
    return fuzzy_ratio(prediction, expected) >= threshold


def score(
    method: ScoringMethod,
    prediction: str,
    expected: list[str],
    threshold: float | None = None,
) -> bool:
    if method is ScoringMethod.EXACT:
        return exact_match(prediction, expected)
    if method is ScoringMethod.NORMALIZED:
        return normalized_match(prediction, expected)
    if threshold is None:
        raise ValueError("threshold is required for fuzzy scoring")
    return fuzzy_match(prediction, expected, threshold)
