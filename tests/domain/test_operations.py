from fractions import Fraction

import pytest

from armath.domain import Operation


@pytest.mark.parametrize(
    ("operation", "left", "right", "expected"),
    [
        (Operation.ADD, 47, 38, 85),
        (Operation.SUBTRACT, 30, 45, -15),
        (Operation.MULTIPLY, 12, 7, 84),
        (Operation.DIVIDE, 7, 2, Fraction(7, 2)),
    ],
)
def test_apply(operation: Operation, left: int, right: int, expected: Fraction) -> None:
    assert operation.apply(Fraction(left), Fraction(right)) == expected


def test_apply_is_exact_for_decimals() -> None:
    assert Operation.ADD.apply(Fraction("0.1"), Fraction("0.2")) == Fraction("0.3")


def test_divide_by_zero_raises() -> None:
    with pytest.raises(ZeroDivisionError):
        Operation.DIVIDE.apply(Fraction(1), Fraction(0))


def test_symbols() -> None:
    assert [operation.symbol for operation in Operation] == ["+", "−", "×", "÷"]
