import pytest
from factories import problem

from armath.analytics import kind_of
from armath.domain import Operand, Operation, Problem


@pytest.mark.parametrize(
    ("left", "operation", "right", "label"),
    [
        (47, Operation.ADD, 38, "2-digit + 2-digit, carrying"),
        (41, Operation.ADD, 38, "2-digit + 2-digit"),
        (1, Operation.ADD, 38, "2-digit + 1-digit"),
        (132, Operation.SUBTRACT, 87, "3-digit − 2-digit, borrowing"),
        (138, Operation.SUBTRACT, 27, "3-digit − 2-digit"),
        (74, Operation.MULTIPLY, 9, "1-digit × 2-digit"),
        (12, Operation.MULTIPLY, 47, "2-digit × 2-digit"),
        (648, Operation.DIVIDE, 12, "3-digit ÷ 2-digit"),
    ],
)
def test_kind_labels(left: int, operation: Operation, right: int, label: str) -> None:
    kind = kind_of(problem(left, operation, right))

    assert kind is not None
    assert kind.label == label
    assert kind.operation is operation


def test_multiplication_kind_ignores_factor_order() -> None:
    assert kind_of(problem(7, Operation.MULTIPLY, 68)) == kind_of(
        problem(68, Operation.MULTIPLY, 7)
    )


def test_kinds_sort_by_operation() -> None:
    kinds = [
        kind_of(problem(648, Operation.DIVIDE, 12)),
        kind_of(problem(47, Operation.ADD, 38)),
    ]

    assert sorted(k for k in kinds if k is not None)[0].operation is Operation.ADD


def test_decimal_problems_have_no_kind() -> None:
    decimal = Problem.create(Operand.decimal("1.5"), Operation.ADD, Operand.integer(2))

    assert kind_of(decimal) is None
