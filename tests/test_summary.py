import pytest
from factories import attempt, problem, record

from armath.analytics import SlowProblem, summarize
from armath.domain import Operation


def test_summary_of_a_session() -> None:
    summary = summarize(
        record(
            attempt(problem(2, Operation.ADD, 2), seconds=1.0),
            attempt(problem(12, Operation.MULTIPLY, 13), seconds=6.0),
            attempt(problem(9, Operation.SUBTRACT, 4), correct=False, seconds=2.0),
        ),
        slowest=2,
    )

    assert summary.answered == 3
    assert summary.correct == 2
    assert summary.accuracy == pytest.approx(2 / 3)
    assert summary.mean_seconds == pytest.approx(3.0)
    assert summary.slowest == (
        SlowProblem("12 × 13 = 156", 6.0),
        SlowProblem("9 − 4 = 5", 2.0),
    )


def test_summary_of_an_empty_session() -> None:
    summary = summarize(record())

    assert summary.answered == 0
    assert summary.accuracy is None
    assert summary.mean_seconds is None
    assert summary.slowest == ()
