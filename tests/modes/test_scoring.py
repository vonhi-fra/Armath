from datetime import UTC, datetime
from fractions import Fraction

from armath.domain import Attempt, Operand, Operation, Problem
from armath.modes import CorrectCount, CorrectMinusWrong

PROBLEM = Problem.create(Operand.integer(6), Operation.MULTIPLY, Operand.integer(7))
NOW = datetime(2026, 9, 29, tzinfo=UTC)
RIGHT = Attempt(PROBLEM, Fraction(42), 2.0, NOW)
WRONG = Attempt(PROBLEM, Fraction(48), 2.0, NOW)


def test_correct_count() -> None:
    assert CorrectCount().score([RIGHT, WRONG, RIGHT]) == 2


def test_correct_minus_wrong() -> None:
    assert CorrectMinusWrong().score([RIGHT, WRONG, RIGHT]) == 1


def test_custom_penalty() -> None:
    assert CorrectMinusWrong(penalty=2).score([RIGHT, WRONG, WRONG]) == -3


def test_empty_session_scores_zero() -> None:
    assert CorrectCount().score([]) == 0
    assert CorrectMinusWrong().score([]) == 0
