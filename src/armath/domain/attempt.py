"""The record of one answer the user gave."""

from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction

from armath.domain.problem import Problem


@dataclass(frozen=True)
class Attempt:
    """A response to a problem and how it was given.

    Times are measured from when the problem was shown. ``first_input_seconds`` (when the first
    character was typed) separates thinking from typing; ``corrections`` counts how often the
    user deleted what they had typed, which is the only error signal in modes that wait for the
    correct answer.
    """

    problem: Problem
    response: Fraction
    elapsed_seconds: float
    answered_at: datetime
    first_input_seconds: float | None = None
    corrections: int = 0

    def __post_init__(self) -> None:
        if self.elapsed_seconds < 0:
            raise ValueError("elapsed time cannot be negative")
        if self.first_input_seconds is not None and self.first_input_seconds < 0:
            raise ValueError("first input time cannot be negative")
        if self.corrections < 0:
            raise ValueError("corrections cannot be negative")
        if self.answered_at.tzinfo is None:
            raise ValueError("answered_at must be timezone-aware")

    @property
    def is_correct(self) -> bool:
        return self.problem.is_correct(self.response)

    @property
    def is_clean(self) -> bool:
        """Correct at the first try, without deleting anything."""
        return self.is_correct and self.corrections == 0
