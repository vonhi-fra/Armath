"""Division tricks for exact whole-number division, as in Zetamac's reversed multiplication."""

from collections.abc import Sequence
from fractions import Fraction
from random import Random

from armath.domain import Operation
from armath.tricks.base import WholeNumberTrick
from armath.tricks.explanation import Step, calc
from armath.tricks.multiplication import TIMES_TABLE_LIMIT

MUL, DIV, ADD, SUB = Operation.MULTIPLY, Operation.DIVIDE, Operation.ADD, Operation.SUBTRACT


def _exact_quotient(dividend: int, divisor: int) -> int | None:
    if divisor <= 0 or dividend % divisor:
        return None
    return dividend // divisor


class ChunkingDivision(WholeNumberTrick):
    id = "div-chunk"
    name = "Missing factor"
    summary = "Think “divisor × ? = dividend”: take the biggest round multiple, then the rest."
    operation = DIV
    priority = 0
    fallback = True

    def fits(self, left: int, right: int) -> bool:
        return _exact_quotient(left, right) is not None

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        quotient = left // right
        round_part, table_part = quotient - quotient % 10, quotient % 10
        if round_part == 0:
            return [_recall(right, table_part)]
        chunk = calc(f"Biggest round multiple of {right}", right, MUL, round_part)
        if table_part == 0:
            return [
                chunk,
                Step("Nothing is left", f"{left} ÷ {right} = {round_part}", _f(round_part)),
            ]
        rest = calc("What is left", left, SUB, chunk.value)
        return [
            chunk,
            rest,
            _recall(right, table_part),
            calc("Add the pieces", round_part, ADD, table_part),
        ]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        divisor = rng.randint(3, 12)
        return divisor * rng.randint(13, 99), divisor


class DivideByFive(WholeNumberTrick):
    id = "div-5"
    name = "÷5 = ×2, then ÷10"
    summary = "Dividing by 5 is doubling and dropping a zero."
    operation = DIV
    priority = 80

    def fits(self, left: int, right: int) -> bool:
        quotient = _exact_quotient(left, right)
        return right == 5 and quotient is not None and quotient > TIMES_TABLE_LIMIT

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        double = calc(f"Double {left}", left, MUL, 2)
        return [double, calc("Drop the zero", double.value, DIV, 10)]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        return 5 * rng.randint(13, 100), 5


class HalveBoth(WholeNumberTrick):
    id = "div-halve-both"
    name = "Halve both"
    summary = "If both numbers are even, halve both until the division is easy."
    operation = DIV
    priority = 50

    def fits(self, left: int, right: int) -> bool:
        quotient = _exact_quotient(left, right)
        return (
            quotient is not None
            and quotient > TIMES_TABLE_LIMIT
            and right >= 4
            and right % 2 == 0
            and left % 2 == 0
        )

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        steps = []
        dividend, divisor = left, right
        while divisor > 2 and divisor % 2 == 0 and dividend % 2 == 0:
            halved = dividend // 2, divisor // 2
            steps.append(
                Step(
                    "Halve both",
                    f"{dividend} ÷ {divisor} → {halved[0]} ÷ {halved[1]}",
                    Fraction(*halved),
                )
            )
            dividend, divisor = halved
        steps.append(calc("Now divide", dividend, DIV, divisor))
        return steps

    def example_operands(self, rng: Random) -> tuple[int, int]:
        divisor = rng.choice((4, 6, 8, 12))
        return divisor * rng.randint(13, 99), divisor


class DivideByEleven(WholeNumberTrick):
    id = "div-11"
    name = "÷11 from the outer digits"
    summary = (
        "The quotient is the first and last digit; if the first digit is bigger than the "
        "middle one, take 1 off it."
    )
    operation = DIV
    priority = 90

    def fits(self, left: int, right: int) -> bool:
        quotient = _exact_quotient(left, right)
        return right == 11 and quotient is not None and 10 <= quotient <= 99

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        front, middle, last = left // 100, left // 10 % 10, left % 10
        if front > middle:
            tens = front - 1
            first = Step(
                f"{front} is bigger than the middle digit {middle}, so there was a carry",
                f"{front} − 1 = {tens}",
                _f(tens),
            )
        else:
            tens = front
            first = Step("The first digit is the tens", f"{left} → {tens}", _f(tens))
        result = tens * 10 + last
        return [
            first,
            Step("The last digit is the units", f"{left} → {last}", _f(last)),
            Step("Put them together", f"{tens} | {last} → {result}", _f(result)),
        ]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        return 11 * rng.randint(12, 99), 11


class DivideByNine(WholeNumberTrick):
    id = "div-9"
    name = "÷9 digit rule"
    summary = (
        "Cover the last digit and see how many 9s fit: that's the tens. "
        "The units are 10 − the last digit."
    )
    operation = DIV
    priority = 85

    def fits(self, left: int, right: int) -> bool:
        quotient = _exact_quotient(left, right)
        return right == 9 and quotient is not None and quotient >= 10 and quotient % 10 != 0

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        rest, last = divmod(left, 10)
        tens = rest // 9
        units = calc(f"The units are 10 minus the last digit {last}", 10, SUB, last)
        result = tens * 10 + int(units.value)
        return [
            Step(f"Cover the last digit of {left}", f"{left} → {rest}", _f(rest)),
            Step(f"Count how many 9s fit in {rest}", f"9 × {tens} ≤ {rest} → {tens}", _f(tens)),
            units,
            Step("Put them together", f"{tens} | {units.value} → {result}", _f(result)),
        ]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        quotient = rng.randint(1, 9) * 10 + rng.randint(1, 9)
        return 9 * quotient, 9


def _recall(divisor: int, quotient: int) -> Step:
    product = divisor * quotient
    return Step(
        "Recall the times table",
        f"{divisor} × {quotient} = {product}, so {product} ÷ {divisor} = {quotient}",
        _f(quotient),
    )


def _f(value: int) -> Fraction:
    return Fraction(value)
