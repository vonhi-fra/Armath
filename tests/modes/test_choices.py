from fractions import Fraction
from random import Random

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from armath.domain import Operand, Operation, Problem
from armath.generators import optiver_generator
from armath.modes import PlausibleChoices


def _problem(left: Operand, right: Operand, operation: Operation = Operation.MULTIPLY) -> Problem:
    return Problem.create(left, operation, right)


@settings(max_examples=300)
@given(seed=st.integers())
def test_exactly_one_option_is_right_and_options_are_distinct(seed: int) -> None:
    rng = Random(seed)
    problem = optiver_generator().generate(rng)

    options = PlausibleChoices().choices(problem, rng)

    values = [option.value for option in options]
    assert len(options) == 4
    assert len(set(values)) == 4
    assert sum(problem.is_correct(value) for value in values) == 1
    if problem.answer.value > 0:
        assert all(value > 0 for value in values)


def test_decimal_distractors_look_like_real_slips() -> None:
    problem = _problem(Operand.integer(66), Operand.decimal("2.1"))  # 138.6
    close_or_slipped = {
        Fraction("138.4"),
        Fraction("138.5"),
        Fraction("138.7"),
        Fraction("138.8"),
        Fraction("137.6"),
        Fraction("139.6"),
        Fraction("1386"),
        Fraction("13.86"),
    }

    for seed in range(20):
        options = PlausibleChoices().choices(problem, Random(seed))
        wrong = {o.value for o in options} - {problem.answer.value}
        assert wrong <= close_or_slipped


def test_options_are_written_like_the_answer() -> None:
    problem = _problem(Operand.fraction(3, 8), Operand.fraction(1, 4), Operation.ADD)  # 5/8

    options = PlausibleChoices().choices(problem, Random(0))

    assert all("/" in str(option) for option in options if option.value.denominator > 1)


def test_small_answers_are_padded_with_neighbours() -> None:
    problem = _problem(Operand.integer(1), Operand.integer(1))  # answer 1: few close values

    options = PlausibleChoices().choices(problem, Random(0))

    assert len({o.value for o in options}) == 4
    assert all(o.value > 0 for o in options)


def test_needs_at_least_two_options() -> None:
    with pytest.raises(ValueError, match="at least two"):
        PlausibleChoices(options=1)
