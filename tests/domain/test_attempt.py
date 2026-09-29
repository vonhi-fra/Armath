from datetime import UTC, datetime
from fractions import Fraction

import pytest

from armath.domain import Attempt, Operand, Operation, Problem

PROBLEM = Problem.create(Operand.integer(12), Operation.MULTIPLY, Operand.integer(7))
NOW = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)


def test_correct_attempt() -> None:
    assert Attempt(PROBLEM, Fraction(84), 1.8, NOW).is_correct


def test_wrong_attempt() -> None:
    assert not Attempt(PROBLEM, Fraction(74), 1.8, NOW).is_correct


def test_rejects_negative_elapsed_time() -> None:
    with pytest.raises(ValueError, match="negative"):
        Attempt(PROBLEM, Fraction(84), -0.1, NOW)


def test_clean_means_correct_without_corrections() -> None:
    assert Attempt(PROBLEM, Fraction(84), 1.8, NOW).is_clean
    assert not Attempt(PROBLEM, Fraction(84), 1.8, NOW, corrections=1).is_clean
    assert not Attempt(PROBLEM, Fraction(74), 1.8, NOW).is_clean


@pytest.mark.parametrize(
    ("first_input", "corrections"),
    [(-0.1, 0), (None, -1)],
)
def test_rejects_negative_typing_details(first_input: float | None, corrections: int) -> None:
    with pytest.raises(ValueError, match="negative"):
        Attempt(PROBLEM, Fraction(84), 1.8, NOW, first_input, corrections)


def test_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        Attempt(PROBLEM, Fraction(84), 1.8, datetime(2026, 9, 29, 12, 0))
