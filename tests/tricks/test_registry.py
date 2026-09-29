from fractions import Fraction
from random import Random

import pytest

from armath.domain import Operand, Operation, Problem, Unknown
from armath.tricks import Explanation, Step, TrickRegistry, calc, default_registry
from armath.tricks.multiplication import SplitMultiplication

REGISTRY = default_registry()
TWELVE_TIMES_SEVEN = Problem.create(Operand.integer(12), Operation.MULTIPLY, Operand.integer(7))


def test_ids_must_be_unique() -> None:
    with pytest.raises(ValueError, match="unique"):
        TrickRegistry([SplitMultiplication(), SplitMultiplication()])


def test_unknown_id_raises() -> None:
    with pytest.raises(KeyError):
        REGISTRY.get("no-such-trick")


def test_applicable_is_sorted_best_first() -> None:
    problem = Problem.create(Operand.integer(11), Operation.MULTIPLY, Operand.integer(68))

    priorities = [trick.priority for trick in REGISTRY.applicable(problem)]

    assert priorities == sorted(priorities, reverse=True)
    assert len(priorities) >= 3  # ×11, round up, split


@pytest.mark.parametrize(
    "problem",
    [
        Problem.create(Operand.decimal("1.5"), Operation.ADD, Operand.integer(2)),
        Problem.create(Operand.integer(-3), Operation.ADD, Operand.integer(2)),
        Problem.create(
            Operand.integer(12), Operation.MULTIPLY, Operand.integer(7), unknown=Unknown.LEFT
        ),
        Problem.create(Operand.integer(7), Operation.DIVIDE, Operand.integer(2)),
    ],
    ids=["decimal", "negative", "missing-operand", "inexact-division"],
)
def test_problems_outside_whole_number_tricks_get_no_explanation(problem: Problem) -> None:
    assert REGISTRY.best(problem) is None
    assert REGISTRY.explain(problem) is None


def test_explaining_a_problem_the_trick_does_not_fit_raises() -> None:
    with pytest.raises(ValueError, match="does not apply"):
        REGISTRY.get("mul-11").explain(TWELVE_TIMES_SEVEN)


def test_explanation_must_end_at_the_answer() -> None:
    wrong = calc("Guess", 12, Operation.MULTIPLY, 6)

    with pytest.raises(ValueError, match="but the answer is 84"):
        Explanation("guess", TWELVE_TIMES_SEVEN, (wrong,))


def test_explanation_needs_steps() -> None:
    with pytest.raises(ValueError, match="at least one step"):
        Explanation("empty", TWELVE_TIMES_SEVEN, ())


def test_calc_formats_exact_values() -> None:
    assert calc("Halve", 7, Operation.DIVIDE, 2) == Step("Halve", "7 ÷ 2 = 3.5", Fraction(7, 2))
    assert calc("Third", 1, Operation.DIVIDE, 3).work == "1 ÷ 3 = 1/3"


def test_trick_generates_problems_like_a_generator() -> None:
    problem = REGISTRY.get("mul-11").generate(Random(0))

    assert 11 in (problem.left.value, problem.right.value)
