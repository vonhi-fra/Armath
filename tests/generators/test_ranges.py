from random import Random

import pytest
from hypothesis import given
from hypothesis import strategies as st

from armath.generators import IntRange


def test_rejects_empty_range() -> None:
    with pytest.raises(ValueError, match="empty range"):
        IntRange(5, 4)


def test_contains_is_inclusive() -> None:
    digits = IntRange(0, 9)

    assert 0 in digits
    assert 9 in digits
    assert 10 not in digits


@given(st.integers(-1000, 1000), st.integers(0, 1000), st.integers())
def test_samples_stay_inside_the_range(low: int, width: int, seed: int) -> None:
    int_range = IntRange(low, low + width)

    assert int_range.sample(Random(seed)) in int_range
