"""Addition tricks."""

from collections.abc import Sequence
from random import Random

from armath.domain import Operation
from armath.tricks.base import WholeNumberTrick
from armath.tricks.explanation import Step, calc


class LeftToRightAddition(WholeNumberTrick):
    id = "add-left-to-right"
    name = "Left to right"
    summary = "Add the tens first, then the units, and start typing early."
    operation = Operation.ADD
    priority = 0
    fallback = True

    def fits(self, left: int, right: int) -> bool:
        return True

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        big, small = max(left, right), min(left, right)
        tens, units = small - small % 10, small % 10
        if tens == 0 or units == 0:
            return [calc("Add them", big, Operation.ADD, small)]
        after_tens = big + tens
        return [
            calc(f"Add the tens of {small}", big, Operation.ADD, tens),
            calc("Then the units", after_tens, Operation.ADD, units),
        ]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        return rng.randint(12, 99), rng.randint(12, 99)


class RoundUpAddition(WholeNumberTrick):
    id = "add-round-up"
    name = "Round and compensate"
    summary = "An addend ending in 7, 8 or 9: add the next round number, then take the extra back."
    operation = Operation.ADD
    priority = 40

    def fits(self, left: int, right: int) -> bool:
        return bool(_round_candidates(left, right))

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        # Round the addend closest to its next ten.
        near, other = max(_round_candidates(left, right), key=lambda pair: (pair[0] % 10, pair[0]))
        extra = 10 - near % 10
        rounded = near + extra
        sum_rounded = other + rounded
        return [
            calc(f"Round {near} up to {rounded}", other, Operation.ADD, rounded),
            calc(f"Take back the extra {extra}", sum_rounded, Operation.SUBTRACT, extra),
        ]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        near = rng.randint(1, 9) * 10 + rng.randint(7, 9)
        other = rng.randint(2, 100)
        return (near, other) if rng.random() < 0.5 else (other, near)


def _round_candidates(left: int, right: int) -> list[tuple[int, int]]:
    """(addend worth rounding up, the other addend) pairs.

    Only for sums below 1000: with bigger numbers, left to right is simpler.
    """
    if max(left, right) >= 1000:
        return []
    return [(n, other) for n, other in ((left, right), (right, left)) if near_next_ten(n)]


def near_next_ten(value: int) -> bool:
    """At least two digits and ending in 7, 8 or 9."""
    return value >= 10 and value % 10 >= 7
