import pytest
from factories import attempt, problem, record

from armath.analytics import SlowProblem, first_try_rate, summarize
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
    assert summary.first_try_rate == pytest.approx(2 / 3)
    assert summary.mean_seconds == pytest.approx(3.0)
    assert summary.slowest == (
        SlowProblem("12 × 13 = 156", 6.0),
        SlowProblem("9 − 4 = 5", 2.0),
    )


def test_summary_of_an_empty_session() -> None:
    summary = summarize(record())

    assert summary.answered == 0
    assert summary.first_try_rate is None
    assert summary.mean_seconds is None
    assert summary.slowest == ()


def test_corrected_answers_do_not_count_as_first_try() -> None:
    attempts = [attempt(), attempt(corrections=1), attempt(correct=False), attempt()]

    assert first_try_rate(attempts) == 0.5
