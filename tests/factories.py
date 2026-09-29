"""Shared builders for test data."""

from datetime import UTC, datetime, timedelta
from fractions import Fraction

from armath.domain import Attempt, Operand, Operation, Problem, SessionRecord

START = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)


def problem(left: int = 6, operation: Operation = Operation.MULTIPLY, right: int = 7) -> Problem:
    return Problem.create(Operand.integer(left), operation, Operand.integer(right))


def attempt(
    the_problem: Problem | None = None,
    *,
    correct: bool = True,
    seconds: float = 2.0,
    corrections: int = 0,
) -> Attempt:
    the_problem = the_problem or problem()
    answer = the_problem.answer.value
    return Attempt(
        problem=the_problem,
        response=answer if correct else answer + Fraction(1),
        elapsed_seconds=seconds,
        answered_at=START + timedelta(seconds=seconds),
        first_input_seconds=seconds / 2,
        corrections=corrections,
    )


def record(
    *attempts: Attempt, mode: str = "Zetamac 120s", score: int | None = None
) -> SessionRecord:
    return SessionRecord(
        mode=mode,
        started_at=START,
        score=sum(a.is_correct for a in attempts) if score is None else score,
        attempts=attempts,
    )
