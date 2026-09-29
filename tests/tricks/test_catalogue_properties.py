"""Invariants every trick in the catalogue must satisfy, checked on many random problems."""

from random import Random

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from armath.domain import Operand, Operation, Problem
from armath.generators import ZetamacSettings, zetamac_generator
from armath.tricks import Trick, default_registry

REGISTRY = default_registry()


@pytest.mark.parametrize("trick", REGISTRY.all(), ids=lambda trick: trick.id)
@settings(max_examples=60)
@given(seed=st.integers())
def test_practice_problems_fit_the_trick_and_are_explained(trick: Trick, seed: int) -> None:
    problem = trick.generate(Random(seed))

    assert trick.applies_to(problem)
    explanation = trick.explain(problem)
    assert explanation.result == problem.answer.value
    assert all(step.label and step.work for step in explanation.steps)


def _whole_problem(operation: Operation, a: int, b: int) -> Problem:
    if operation is Operation.DIVIDE:  # exact division: a is the quotient, b the divisor
        return Problem.create(Operand.integer(a * b), operation, Operand.integer(b))
    return Problem.create(Operand.integer(a), operation, Operand.integer(b))


@settings(max_examples=500)
@given(
    operation=st.sampled_from(Operation),
    a=st.integers(0, 1200),
    b=st.integers(1, 150),
)
def test_every_applicable_trick_explains_any_whole_number_problem(
    operation: Operation, a: int, b: int
) -> None:
    problem = _whole_problem(operation, a, b)

    tricks = REGISTRY.applicable(problem)

    assert tricks, f"no trick covers {problem.prompt}"
    assert tricks[-1].fallback
    for trick in tricks:
        assert trick.explain(problem).result == problem.answer.value


@settings(max_examples=300)
@given(seed=st.integers())
def test_every_zetamac_problem_has_an_explanation(seed: int) -> None:
    problem = zetamac_generator(ZetamacSettings()).generate(Random(seed))

    explanation = REGISTRY.explain(problem)

    assert explanation is not None
    assert explanation.result == problem.answer.value


@pytest.mark.parametrize("operation", Operation)
def test_each_operation_has_exactly_one_fallback(operation: Operation) -> None:
    fallbacks = [trick for trick in REGISTRY.for_operation(operation) if trick.fallback]

    assert len(fallbacks) == 1
    assert fallbacks[0].priority < min(
        trick.priority for trick in REGISTRY.for_operation(operation) if not trick.fallback
    )


def test_every_trick_has_descriptive_metadata() -> None:
    for trick in REGISTRY.all():
        assert trick.id
        assert trick.name
        assert trick.summary
