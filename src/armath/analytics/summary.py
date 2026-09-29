"""Headline numbers for one finished session."""

from collections.abc import Sequence
from dataclasses import dataclass
from statistics import fmean

from armath.domain import Attempt, SessionRecord


@dataclass(frozen=True)
class SlowProblem:
    equation: str
    seconds: float


@dataclass(frozen=True)
class SessionSummary:
    mode: str
    score: int
    answered: int
    first_try_rate: float | None
    mean_seconds: float | None
    slowest: tuple[SlowProblem, ...]


def first_try_rate(attempts: Sequence[Attempt]) -> float | None:
    """Share of answers that were right without any correction; ``None`` if there are none.

    In Zetamac-style modes only correct answers are submitted, so corrections are the
    only visible mistakes.
    """
    if not attempts:
        return None
    return sum(attempt.is_clean for attempt in attempts) / len(attempts)


def summarize(record: SessionRecord, slowest: int = 5) -> SessionSummary:
    attempts = record.attempts
    by_time = sorted(attempts, key=lambda attempt: attempt.elapsed_seconds, reverse=True)
    return SessionSummary(
        mode=record.mode,
        score=record.score,
        answered=len(attempts),
        first_try_rate=first_try_rate(attempts),
        mean_seconds=fmean(a.elapsed_seconds for a in attempts) if attempts else None,
        slowest=tuple(
            SlowProblem(a.problem.equation, a.elapsed_seconds) for a in by_time[:slowest]
        ),
    )
