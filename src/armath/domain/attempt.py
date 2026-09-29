"""The record of one answer the user gave."""

from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction

from armath.domain.problem import Problem


@dataclass(frozen=True)
class Attempt:
    """A response to a problem and how long it took, measured from when it was shown."""

    problem: Problem
    response: Fraction
    elapsed_seconds: float
    answered_at: datetime

    def __post_init__(self) -> None:
        if self.elapsed_seconds < 0:
            raise ValueError("elapsed time cannot be negative")
        if self.answered_at.tzinfo is None:
            raise ValueError("answered_at must be timezone-aware")

    @property
    def is_correct(self) -> bool:
        return self.problem.is_correct(self.response)
