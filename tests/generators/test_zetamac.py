from random import Random

import pytest
from hypothesis import given
from hypothesis import strategies as st

from armath.domain import Operation, Unknown
from armath.generators import IntRange, ZetamacSettings, zetamac_generator


@given(st.integers())
def test_default_problems_match_zetamac_ranges(seed: int) -> None:
    problem = zetamac_generator(ZetamacSettings()).generate(Random(seed))
    left, right, answer = (int(o.value) for o in (problem.left, problem.right, problem.answer))

    assert problem.unknown is Unknown.RESULT
    match problem.operation:
        case Operation.ADD:
            assert left in IntRange(2, 100)
            assert right in IntRange(2, 100)
        case Operation.SUBTRACT:
            assert right in IntRange(2, 100)
            assert answer in IntRange(2, 100)
        case Operation.MULTIPLY:
            assert left in IntRange(2, 12)
            assert right in IntRange(2, 100)
        case Operation.DIVIDE:
            assert right in IntRange(2, 12)
            assert answer in IntRange(2, 100)


def test_only_enabled_operations_appear() -> None:
    settings = ZetamacSettings(operations=frozenset({Operation.MULTIPLY, Operation.DIVIDE}))
    generator = zetamac_generator(settings)
    rng = Random(1)

    operations = {generator.generate(rng).operation for _ in range(200)}

    assert operations == {Operation.MULTIPLY, Operation.DIVIDE}


def test_same_seed_gives_same_problems() -> None:
    generator = zetamac_generator(ZetamacSettings())
    first, second = Random(42), Random(42)

    assert [generator.generate(first) for _ in range(20)] == [
        generator.generate(second) for _ in range(20)
    ]


def test_needs_an_operation() -> None:
    with pytest.raises(ValueError, match="at least one operation"):
        ZetamacSettings(operations=frozenset())


def test_division_needs_nonzero_divisors() -> None:
    with pytest.raises(ValueError, match="without 0"):
        ZetamacSettings(multiplication_left=IntRange(0, 12))


def test_zero_is_fine_without_division() -> None:
    settings = ZetamacSettings(
        multiplication_left=IntRange(0, 12),
        operations=frozenset({Operation.MULTIPLY}),
    )

    assert zetamac_generator(settings).generate(Random(0)).operation is Operation.MULTIPLY
