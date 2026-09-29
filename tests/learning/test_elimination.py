from fractions import Fraction

import pytest
from factories import problem

from armath.domain import Operand, Operation, Problem, Unknown
from armath.learning.elimination import rule_out


@pytest.mark.parametrize(
    ("the_problem", "chosen", "reason"),
    [
        (
            problem(18, Operation.MULTIPLY, 41),
            Fraction(7380),
            "Estimate: 20 × 40 ≈ 800, so 7380 is about 10 times too big.",
        ),
        (
            Problem.create(Operand.decimal("17.1"), Operation.DIVIDE, Operand.integer(9)),
            Fraction("0.19"),
            "Estimate: 20 ÷ 9 ≈ 2.2, so 0.19 is about 10 times too small.",
        ),
        (
            problem(4488, Operation.ADD, 332),
            Fraction(4822),
            "Last digits: 8 + 2 → the answer ends in 0, but 4822 ends in 2.",
        ),
        (
            problem(93, Operation.SUBTRACT, 48),
            Fraction(44),
            "Last digits: 3 − 8 → the answer ends in 5, but 44 ends in 4.",
        ),
        (
            problem(7, Operation.MULTIPLY, 68),
            Fraction(474),
            "Last digits: 7 × 8 → the answer ends in 6, but 474 ends in 4.",
        ),
        (
            Problem.create(
                Operand.integer(66),
                Operation.MULTIPLY,
                Operand.decimal("2.1"),
                unknown=Unknown.RIGHT,
            ),
            Fraction(21),
            "Estimate: 100 ÷ 70 ≈ 1.4, so 21 is about 10 times too big.",
        ),
    ],
)
def test_rule_out(the_problem: Problem, chosen: Fraction, reason: str) -> None:
    assert rule_out(the_problem, chosen) == reason


@pytest.mark.parametrize(
    ("the_problem", "chosen"),
    [
        (problem(7, Operation.MULTIPLY, 68), Fraction(476)),  # the right answer
        (problem(7, Operation.MULTIPLY, 68), Fraction(486)),  # same last digit, same size
        (problem(648, Operation.DIVIDE, 12), Fraction(55)),  # no last-digit rule for division
    ],
)
def test_no_quick_check(the_problem: Problem, chosen: Fraction) -> None:
    assert rule_out(the_problem, chosen) is None
