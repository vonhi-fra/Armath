"""How a finished list of attempts turns into a score."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from armath.domain import Attempt


class ScoringPolicy(Protocol):
    def score(self, attempts: Sequence[Attempt]) -> int: ...


@dataclass(frozen=True)
class CorrectCount:
    """One point per correct answer (Zetamac)."""

    def score(self, attempts: Sequence[Attempt]) -> int:
        return sum(attempt.is_correct for attempt in attempts)


@dataclass(frozen=True)
class CorrectMinusWrong:
    """One point per correct answer, minus ``penalty`` per wrong one (Optiver 80-in-8)."""

    penalty: int = 1

    def score(self, attempts: Sequence[Attempt]) -> int:
        correct = sum(attempt.is_correct for attempt in attempts)
        return correct - self.penalty * (len(attempts) - correct)
