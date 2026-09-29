"""Subtraction tricks."""

from collections.abc import Sequence
from random import Random

from armath.domain import Operation
from armath.tricks.addition import near_next_ten
from armath.tricks.base import WholeNumberTrick
from armath.tricks.explanation import Step, calc


class LeftToRightSubtraction(WholeNumberTrick):
    id = "sub-left-to-right"
    name = "Left to right"
    summary = "Subtract the tens first, then the units."
    operation = Operation.SUBTRACT
    priority = 0
    fallback = True

    def fits(self, left: int, right: int) -> bool:
        return True

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        tens, units = right - right % 10, right % 10
        if tens == 0 or units == 0:
            return [calc("Subtract", left, Operation.SUBTRACT, right)]
        after_tens = left - tens
        return [
            calc(f"Subtract the tens of {right}", left, Operation.SUBTRACT, tens),
            calc("Then the units", after_tens, Operation.SUBTRACT, units),
        ]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        right = rng.randint(12, 99)
        return right + rng.randint(2, 100), right


class RoundUpSubtraction(WholeNumberTrick):
    id = "sub-round-up"
    name = "Round and compensate"
    summary = "Subtracting a number ending in 7, 8 or 9: subtract the next round number, add back."
    operation = Operation.SUBTRACT
    priority = 55

    def fits(self, left: int, right: int) -> bool:
        return near_next_ten(right)

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        extra = 10 - right % 10
        rounded = right + extra
        after_round = left - rounded
        return [
            calc(f"Round {right} up to {rounded}", left, Operation.SUBTRACT, rounded),
            calc(f"Add back the extra {extra}", after_round, Operation.ADD, extra),
        ]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        right = rng.randint(1, 9) * 10 + rng.randint(7, 9)
        return right + rng.randint(2, 100), right


class CountUpSubtraction(WholeNumberTrick):
    id = "sub-count-up"
    name = "Count up"
    summary = "When the subtraction crosses a hundred, count up from the smaller number."
    operation = Operation.SUBTRACT
    priority = 50

    def fits(self, left: int, right: int) -> bool:
        return right >= 10 and right % 100 != 0 and _next_hundred(right) <= left

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        hundred = _next_hundred(right)
        to_hundred = calc(f"From {right} up to {hundred}", hundred, Operation.SUBTRACT, right)
        if left == hundred:
            return [to_hundred]
        rest = left - hundred
        return [
            to_hundred,
            calc(f"From {hundred} up to {left}", left, Operation.SUBTRACT, hundred),
            calc("Add the two jumps", to_hundred.value, Operation.ADD, rest),
        ]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        right = rng.randint(11, 99)
        return rng.randint(100, right + 100), right


def _next_hundred(value: int) -> int:
    return (value // 100 + 1) * 100
