from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Category(StrEnum):
    TRANSLATION = "translation"
    QA = "qa"
    SENTIMENT = "sentiment"
    CODE_SWITCHING = "code_switching"
    INSTRUCTION_FOLLOWING = "instruction_following"
    SAFETY_REFUSAL = "safety_refusal"


class ScoringMethod(StrEnum):
    EXACT = "exact"
    NORMALIZED = "normalized"
    FUZZY = "fuzzy"


class ReviewStatus(StrEnum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    REJECTED = "rejected"


class Item(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # "<category>-<3 digits>", the prefix must match `category`
    id: Annotated[str, StringConstraints(pattern=r"^[a-z_]+-\d{3}$")]
    category: Category
    prompt: NonEmptyStr
    expected: Annotated[list[NonEmptyStr], Field(min_length=1)]
    scoring: ScoringMethod
    # only used (and required) when scoring is "fuzzy"
    threshold: Annotated[float, Field(gt=0, le=1)] | None = None
    # ISO 639 codes present in the item: "ary" for Darija, "fr", "en", "ar"
    languages: Annotated[list[NonEmptyStr], Field(min_length=1)]
    notes: str | None = None
    review_status: ReviewStatus

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        prefix = self.id.rsplit("-", 1)[0]
        if prefix != self.category.value:
            raise ValueError(
                f"id prefix {prefix!r} does not match category {self.category.value!r}"
            )
        if self.scoring is ScoringMethod.FUZZY and self.threshold is None:
            raise ValueError("threshold is required when scoring is 'fuzzy'")
        if self.scoring is not ScoringMethod.FUZZY and self.threshold is not None:
            raise ValueError("threshold is only allowed when scoring is 'fuzzy'")
        return self
