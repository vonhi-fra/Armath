"""Headline numbers for one finished session."""

from dataclasses import dataclass
from statistics import fmean

from armath.domain import SessionRecord


@dataclass(frozen=True)
class SlowProblem:
    equation: str
    seconds: float


@dataclass(frozen=True)
class SessionSummary:
    mode: str
    score: int
    answered: int
    correct: int
    accuracy: float | None
    mean_seconds: float | None
    slowest: tuple[SlowProblem, ...]


def summarize(record: SessionRecord, slowest: int = 5) -> SessionSummary:
    attempts = record.attempts
    correct = sum(attempt.is_correct for attempt in attempts)
    by_time = sorted(attempts, key=lambda attempt: attempt.elapsed_seconds, reverse=True)
    return SessionSummary(
        mode=record.mode,
        score=record.score,
        answered=len(attempts),
        correct=correct,
        accuracy=correct / len(attempts) if attempts else None,
        mean_seconds=fmean(a.elapsed_seconds for a in attempts) if attempts else None,
        slowest=tuple(
            SlowProblem(a.problem.equation, a.elapsed_seconds) for a in by_time[:slowest]
        ),
    )
