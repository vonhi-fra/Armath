from collections import Counter
from random import Random

from hypothesis import given, settings
from hypothesis import strategies as st

from armath.domain import NumberStyle, Unknown
from armath.domain.numbers import decimal_places
from armath.generators import optiver_generator
from armath.generators.optiver import FractionOperations, random_decimal


@settings(max_examples=300)
@given(seed=st.integers())
def test_problems_are_positive_and_neat(seed: int) -> None:
    problem = optiver_generator().generate(Random(seed))

    assert problem.answer.value > 0
    for operand in (problem.left, problem.right, problem.result):
        if operand.style is not NumberStyle.FRACTION:
            places = decimal_places(operand.value)
            assert places is not None
            assert places <= 4


def test_mix_covers_every_kind_of_problem() -> None:
    generator = optiver_generator()
    rng = Random(0)
    problems = [generator.generate(rng) for _ in range(800)]

    styles = Counter(p.answer.style for p in problems)
    unknowns = Counter(p.unknown for p in problems)

    assert {NumberStyle.INTEGER, NumberStyle.DECIMAL, NumberStyle.FRACTION} <= set(styles)
    assert 0.15 < (unknowns[Unknown.LEFT] + unknowns[Unknown.RIGHT]) / len(problems) < 0.35


def test_missing_operand_share_can_be_switched_off() -> None:
    generator = optiver_generator(missing_operand_share=0)
    rng = Random(1)

    assert all(generator.generate(rng).unknown is Unknown.RESULT for _ in range(200))


@given(seed=st.integers())
def test_random_decimal_has_the_requested_places(seed: int) -> None:
    assert decimal_places(random_decimal(Random(seed), places=2)) == 2


@given(seed=st.integers())
def test_fraction_problems_use_fractions(seed: int) -> None:
    problem = FractionOperations().generate(Random(seed))

    assert NumberStyle.FRACTION in (problem.left.style, problem.right.style)
