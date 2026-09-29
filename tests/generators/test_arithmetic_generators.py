from random import Random

import pytest
from hypothesis import given
from hypothesis import strategies as st

from armath.domain import Operand, Operation, Problem
from armath.generators import IntRange, InverseGenerator, MixedGenerator, RangeGenerator

SMALL = IntRange(2, 12)


@given(st.integers())
def test_range_generator_draws_operands_from_its_ranges(seed: int) -> None:
    generator = RangeGenerator(Operation.MULTIPLY, IntRange(2, 12), IntRange(50, 60))

    problem = generator.generate(Random(seed))

    assert problem.operation is Operation.MULTIPLY
    assert int(problem.left.value) in IntRange(2, 12)
    assert int(problem.right.value) in IntRange(50, 60)


def test_range_generator_rejects_divisor_range_with_zero() -> None:
    with pytest.raises(ValueError, match="must not contain 0"):
        RangeGenerator(Operation.DIVIDE, SMALL, IntRange(0, 5))


@given(st.integers())
def test_inverse_of_addition_is_subtraction(seed: int) -> None:
    addition = RangeGenerator(Operation.ADD, IntRange(2, 100), IntRange(2, 100))
    rng, same_rng = Random(seed), Random(seed)

    original = addition.generate(rng)
    inverse = InverseGenerator(addition).generate(same_rng)

    assert inverse.operation is Operation.SUBTRACT
    assert inverse.left == original.result
    assert inverse.right == original.left
    assert inverse.answer == original.right


@given(st.integers())
def test_inverse_of_multiplication_is_division_by_the_first_factor(seed: int) -> None:
    multiplication = RangeGenerator(Operation.MULTIPLY, SMALL, IntRange(2, 100))

    problem = InverseGenerator(multiplication).generate(Random(seed))

    assert problem.operation is Operation.DIVIDE
    assert int(problem.right.value) in SMALL
    assert problem.answer.value.denominator == 1


class _FixedGenerator:
    def __init__(self, problem: Problem) -> None:
        self.problem = problem

    def generate(self, rng: Random) -> Problem:
        return self.problem


def test_inverse_rejects_operations_without_inverse() -> None:
    subtraction = Problem.create(Operand.integer(9), Operation.SUBTRACT, Operand.integer(4))

    with pytest.raises(ValueError, match="cannot invert SUBTRACT"):
        InverseGenerator(_FixedGenerator(subtraction)).generate(Random(0))


def test_mixed_generator_uses_every_generator() -> None:
    generators = [RangeGenerator(op, SMALL, SMALL) for op in Operation]
    mixed = MixedGenerator(generators)
    rng = Random(0)

    operations = {mixed.generate(rng).operation for _ in range(200)}

    assert operations == set(Operation)


def test_mixed_generator_needs_a_generator() -> None:
    with pytest.raises(ValueError, match="at least one generator"):
        MixedGenerator([])
