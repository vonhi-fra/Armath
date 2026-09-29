import pytest

from armath.domain import Operand, Operation, parse_problem


@pytest.mark.parametrize(
    ("text", "operation"),
    [
        ("858 / 11", Operation.DIVIDE),
        ("858÷11", Operation.DIVIDE),
        ("67 x 11", Operation.MULTIPLY),
        ("67 X 11", Operation.MULTIPLY),
        ("67*11", Operation.MULTIPLY),
        ("67 × 11 = ?", Operation.MULTIPLY),
        ("132 - 87", Operation.SUBTRACT),
        ("132 − 87 =", Operation.SUBTRACT),
        ("47 + 38", Operation.ADD),
    ],
)
def test_parses_operations(text: str, operation: Operation) -> None:
    assert parse_problem(text).operation is operation


def test_keeps_decimal_notation() -> None:
    problem = parse_problem("8 / 0.4")

    assert problem.right == Operand.decimal("0.4")
    assert problem.prompt == "8 ÷ 0.4 = ?"


@pytest.mark.parametrize("text", ["", "12", "12 x", "a + b", "1 + 2 + 3", "-3 + 4", "5 % 2"])
def test_rejects_non_problems(text: str) -> None:
    with pytest.raises(ValueError, match="not a problem"):
        parse_problem(text)


def test_division_by_zero_is_rejected() -> None:
    with pytest.raises(ValueError, match="division by zero"):
        parse_problem("5 / 0")
