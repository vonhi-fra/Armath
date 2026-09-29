from fractions import Fraction

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from armath.domain import NumberStyle, Operand, Operation, Problem, Unknown


def test_create_computes_result() -> None:
    problem = Problem.create(Operand.integer(12), Operation.MULTIPLY, Operand.integer(7))

    assert problem.result == Operand.integer(84)
    assert problem.answer == Operand.integer(84)
    assert problem.prompt == "12 × 7 = ?"


def test_missing_operand_problem() -> None:
    problem = Problem.create(
        Operand.integer(66), Operation.MULTIPLY, Operand.decimal("2.1"), unknown=Unknown.RIGHT
    )

    assert problem.prompt == "66 × ? = 138.6"
    assert problem.answer == Operand.decimal("2.1")


def test_result_style_is_inferred_from_operands() -> None:
    fraction_sum = Problem.create(Operand.fraction(1, 4), Operation.ADD, Operand.fraction(1, 8))
    decimal_quotient = Problem.create(Operand.integer(7), Operation.DIVIDE, Operand.integer(2))

    assert str(fraction_sum.result) == "3/8"
    assert str(decimal_quotient.result) == "3.5"


def test_explicit_result_style_wins() -> None:
    problem = Problem.create(
        Operand.integer(3),
        Operation.DIVIDE,
        Operand.integer(8),
        result_style=NumberStyle.FRACTION,
    )

    assert str(problem.result) == "3/8"


def test_is_correct_compares_values_not_notation() -> None:
    problem = Problem.create(Operand.integer(1), Operation.DIVIDE, Operand.integer(8))

    assert problem.is_correct(Fraction("0.125"))
    assert problem.is_correct(Fraction(1, 8))
    assert not problem.is_correct(Fraction("0.12"))


def test_rejects_division_by_zero() -> None:
    with pytest.raises(ValueError, match="division by zero"):
        Problem.create(Operand.integer(5), Operation.DIVIDE, Operand.integer(0))


def test_rejects_equation_that_does_not_hold() -> None:
    with pytest.raises(ValueError, match="does not hold"):
        Problem(Operand.integer(2), Operation.ADD, Operand.integer(2), Operand.integer(5))


@pytest.mark.parametrize(
    ("left", "operation", "right", "unknown"),
    [
        (0, Operation.MULTIPLY, 0, Unknown.LEFT),
        (7, Operation.MULTIPLY, 0, Unknown.LEFT),
        (0, Operation.MULTIPLY, 7, Unknown.RIGHT),
        (0, Operation.DIVIDE, 7, Unknown.RIGHT),
    ],
)
def test_rejects_ambiguous_unknown(
    left: int, operation: Operation, right: int, unknown: Unknown
) -> None:
    with pytest.raises(ValueError, match="not uniquely determined"):
        Problem.create(Operand.integer(left), operation, Operand.integer(right), unknown=unknown)


def _solve(problem: Problem) -> Fraction:
    """Recover the hidden value from the visible parts, independently of Problem."""
    left, right, result = problem.left.value, problem.right.value, problem.result.value
    inverse = {
        Operation.ADD: (lambda: result - right, lambda: result - left),
        Operation.SUBTRACT: (lambda: result + right, lambda: left - result),
        Operation.MULTIPLY: (lambda: result / right, lambda: result / left),
        Operation.DIVIDE: (lambda: result * right, lambda: left / result),
    }
    match problem.unknown:
        case Unknown.LEFT:
            return inverse[problem.operation][0]()
        case Unknown.RIGHT:
            return inverse[problem.operation][1]()
        case Unknown.RESULT:
            return result


@given(
    st.integers(-1000, 1000),
    st.sampled_from(Operation),
    st.integers(-1000, 1000),
    st.sampled_from(Unknown),
)
def test_hidden_value_is_the_unique_solution(
    left: int, operation: Operation, right: int, unknown: Unknown
) -> None:
    try:
        problem = Problem.create(
            Operand.integer(left), operation, Operand.integer(right), unknown=unknown
        )
    except ValueError:
        assume(False)
        raise

    assert problem.is_correct(_solve(problem))
    assert problem.prompt.count("?") == 1
