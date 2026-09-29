"""Multiplication tricks, mostly for Zetamac's (2..12) × (2..100)."""

from collections.abc import Sequence
from fractions import Fraction
from random import Random
from typing import ClassVar

from armath.domain import Operation
from armath.tricks.base import WholeNumberTrick, digits, other_factor
from armath.tricks.explanation import Step, calc

MUL, DIV, ADD, SUB = Operation.MULTIPLY, Operation.DIVIDE, Operation.ADD, Operation.SUBTRACT

TIMES_TABLE_LIMIT = 12
"""Products of two factors up to this are recalled, not computed."""

_PLACE_NAMES = {1: "units", 10: "tens", 100: "hundreds", 1000: "thousands"}


def _place_parts(value: int) -> list[tuple[int, str]]:
    """``368`` → ``[(300, "hundreds"), (60, "tens"), (8, "units")]``, skipping zeros."""
    parts = []
    place = 1
    while value:
        value, digit = divmod(value, 10)
        if digit:
            parts.append((digit * place, _PLACE_NAMES.get(place, f"{place}s")))
        place *= 10
    return parts[::-1]


def _small_and_big(left: int, right: int) -> tuple[int, int]:
    return min(left, right), max(left, right)


class SplitMultiplication(WholeNumberTrick):
    id = "mul-split"
    name = "Split and add"
    summary = "Multiply the tens and the units separately, then add, left to right."
    operation = MUL
    priority = 0
    fallback = True

    def fits(self, left: int, right: int) -> bool:
        return True

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        small, big = _small_and_big(left, right)
        parts = _place_parts(big)
        if big <= TIMES_TABLE_LIMIT or len(parts) <= 1:
            return [calc("Times table", small, MUL, big)]
        products = [calc(f"{small} times the {name}", small, MUL, part) for part, name in parts]
        steps = list(products)
        total = products[0].value
        for product in products[1:]:
            add = calc("Add up", total, ADD, product.value)
            steps.append(add)
            total = add.value
        return steps

    def example_operands(self, rng: Random) -> tuple[int, int]:
        return rng.randint(3, 12), rng.randint(13, 99)


class RoundUpMultiplication(WholeNumberTrick):
    id = "mul-round-up"
    name = "Round and compensate"
    summary = (
        "A factor ending in 8 or 9: multiply by the next round number, then take the extra off."
    )
    operation = MUL
    priority = 40

    def fits(self, left: int, right: int) -> bool:
        small, big = _small_and_big(left, right)
        return small >= 2 and big > 10 and big % 10 in (8, 9)

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        small, big = _small_and_big(left, right)
        extra = 10 - big % 10
        rounded = big + extra
        times_rounded = calc(f"Round {big} up to {rounded}", small, MUL, rounded)
        if extra == 1:
            return [
                times_rounded,
                calc(f"Take one {small} back", times_rounded.value, SUB, small),
            ]
        too_much = calc(f"That is {extra} × {small} too much", small, MUL, extra)
        return [
            times_rounded,
            too_much,
            calc("Take it back", times_rounded.value, SUB, too_much.value),
        ]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        return rng.randint(3, 12), rng.randint(1, 9) * 10 + rng.randint(8, 9)


class TimesFive(WholeNumberTrick):
    id = "mul-5"
    name = "×5 = ×10, then halve"
    summary = (
        "Multiplying by 5 is multiplying by 10 and halving (halve first if the number is even)."
    )
    operation = MUL
    priority = 85

    def fits(self, left: int, right: int) -> bool:
        other = other_factor(left, right, 5)
        return other is not None and other > TIMES_TABLE_LIMIT

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        n = other_factor(left, right, 5)
        if n is None:
            raise ValueError("not a ×5 problem")
        if n % 2 == 0:
            half = calc(f"Halve {n}", n, DIV, 2)
            return [half, calc("Times 10", half.value, MUL, 10)]
        tenfold = calc("Times 10", n, MUL, 10)
        return [tenfold, calc("Halve it", tenfold.value, DIV, 2)]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        return 5, rng.randint(13, 100)


class TimesQuarterOrHalfHundred(WholeNumberTrick):
    id = "mul-25-50"
    name = "×25 and ×50"
    summary = "×25 is ×100 ÷ 4 and ×50 is ×100 ÷ 2 (divide first when it goes evenly)."
    operation = MUL
    priority = 85

    _DIVISORS: ClassVar[dict[int, int]] = {25: 4, 50: 2}

    def fits(self, left: int, right: int) -> bool:
        return self._split(left, right) is not None

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        split = self._split(left, right)
        if split is None:
            raise ValueError("not a ×25 or ×50 problem")
        n, factor = split
        divisor = self._DIVISORS[factor]
        if n % divisor == 0:
            part = calc(f"×{factor} is ×100 ÷ {divisor}: divide first", n, DIV, divisor)
            return [part, calc("Times 100", part.value, MUL, 100)]
        hundredfold = calc(f"×{factor} is ×100 ÷ {divisor}", n, MUL, 100)
        return [hundredfold, calc(f"Divide by {divisor}", hundredfold.value, DIV, divisor)]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        return rng.randint(2, 12), rng.choice((25, 50))

    def _split(self, left: int, right: int) -> tuple[int, int] | None:
        """(other factor, 25 or 50)."""
        for factor in self._DIVISORS:
            other = other_factor(left, right, factor)
            if other is not None and other >= 2:
                return other, factor
        return None


class TimesNine(WholeNumberTrick):
    id = "mul-9"
    name = "×9 = ×10 − once"
    summary = "Multiply by 10 (or 100 for ×99), then subtract the number once."
    operation = MUL
    priority = 80

    _ROUND: ClassVar[dict[int, int]] = {9: 10, 99: 100}

    def fits(self, left: int, right: int) -> bool:
        return self._split(left, right) is not None

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        split = self._split(left, right)
        if split is None:
            raise ValueError("not a ×9 or ×99 problem")
        n, factor = split
        round_factor = self._ROUND[factor]
        times_round = calc(f"×{factor} is ×{round_factor} minus once", n, MUL, round_factor)
        return [times_round, calc(f"Subtract {n} once", times_round.value, SUB, n)]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        if rng.random() < 0.8:
            return 9, rng.randint(13, 100)
        return rng.randint(2, 12), 99

    def _split(self, left: int, right: int) -> tuple[int, int] | None:
        """(other factor, 9 or 99), when the other factor is beyond the times table."""
        for factor in self._ROUND:
            other = other_factor(left, right, factor)
            if other is not None and (factor == 99 or other > TIMES_TABLE_LIMIT):
                return other, factor
        return None


class TimesEleven(WholeNumberTrick):
    id = "mul-11"
    name = "×11: digit sum in the middle"
    summary = "For a two-digit number, write the sum of its digits between them (carry if ≥ 10)."
    operation = MUL
    priority = 90

    def fits(self, left: int, right: int) -> bool:
        other = other_factor(left, right, 11)
        return other is not None and 10 <= other <= 99

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        n = other_factor(left, right, 11)
        if n is None:
            raise ValueError("not a ×11 problem")
        tens, units = digits(n)
        digit_sum = calc(f"Add the digits of {n}", tens, ADD, units)
        middle = int(digit_sum.value)
        if middle < 10:
            result = tens * 100 + middle * 10 + units
            return [
                digit_sum,
                Step(
                    f"Write {middle} between {tens} and {units}",
                    f"{tens} | {middle} | {units} → {result}",
                    Fraction(result),
                ),
            ]
        carried = middle - 10
        result = (tens + 1) * 100 + carried * 10 + units
        return [
            digit_sum,
            Step(
                f"{middle} has two digits: write {carried} in the middle and carry 1 to the {tens}",
                f"{tens}+1 | {carried} | {units} → {result}",
                Fraction(result),
            ),
        ]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        # Multiples of 10 (11 × 40) are too easy to be worth practising.
        tens, units = rng.randint(1, 9), rng.randint(1, 9)
        return 11, tens * 10 + units


class TimesTwelve(WholeNumberTrick):
    id = "mul-12"
    name = "×12 = ×10 + ×2"
    summary = "Multiply by 10, add double the number."
    operation = MUL
    priority = 60

    def fits(self, left: int, right: int) -> bool:
        other = other_factor(left, right, 12)
        return other is not None and other > TIMES_TABLE_LIMIT

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        n = other_factor(left, right, 12)
        if n is None:
            raise ValueError("not a ×12 problem")
        tenfold = calc("Times 10", n, MUL, 10)
        double = calc("Double it", n, MUL, 2)
        return [tenfold, double, calc("Add them", tenfold.value, ADD, double.value)]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        return 12, rng.randint(13, 99)


class HalveAndDouble(WholeNumberTrick):
    id = "mul-halve-double"
    name = "Halve and double"
    summary = "An even number times one ending in 5: halve the even one, double the other."
    operation = MUL
    priority = 70

    def fits(self, left: int, right: int) -> bool:
        return self._split(left, right) is not None

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        split = self._split(left, right)
        if split is None:
            raise ValueError("not an even × ...5 problem")
        even, five = split
        half = calc(f"Halve {even}", even, DIV, 2)
        double = calc(f"Double {five}", five, MUL, 2)
        return [half, double, calc("Multiply the easier pair", half.value, MUL, double.value)]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        return rng.choice((2, 4, 6, 8, 12)), rng.randint(1, 9) * 10 + 5

    @staticmethod
    def _split(left: int, right: int) -> tuple[int, int] | None:
        """(even factor, factor ending in 5 of at least two digits)."""
        for even, five in ((left, right), (right, left)):
            if even % 2 == 0 and even > 0 and five % 10 == 5 and five > 10:
                return even, five
        return None


class DoubleRepeatedly(WholeNumberTrick):
    id = "mul-double"
    name = "×4 and ×8 by doubling"
    summary = "×4 is doubling twice, ×8 is doubling three times."
    operation = MUL
    priority = 30

    _DOUBLINGS: ClassVar[dict[int, int]] = {4: 2, 8: 3}

    def fits(self, left: int, right: int) -> bool:
        return self._split(left, right) is not None

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        split = self._split(left, right)
        if split is None:
            raise ValueError("not a ×4 or ×8 problem")
        n, factor = split
        steps = []
        value = n
        for _ in range(self._DOUBLINGS[factor]):
            step = calc("Double", value, MUL, 2)
            steps.append(step)
            value = int(step.value)
        return steps

    def example_operands(self, rng: Random) -> tuple[int, int]:
        return rng.choice((4, 8)), rng.randint(13, 99)

    def _split(self, left: int, right: int) -> tuple[int, int] | None:
        for factor in self._DOUBLINGS:
            other = other_factor(left, right, factor)
            if other is not None and other > TIMES_TABLE_LIMIT:
                return other, factor
        return None


class DifferenceOfSquares(WholeNumberTrick):
    id = "mul-difference-of-squares"
    name = "Difference of squares"
    summary = "Numbers equally far from a round number: (m − d)(m + d) = m² − d²."
    operation = MUL
    priority = 75

    def fits(self, left: int, right: int) -> bool:
        return self._centre(left, right) is not None

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        centre = self._centre(left, right)
        if centre is None:
            raise ValueError("the factors are not equally far from a round number")
        middle, distance = centre
        square = calc(f"{middle} squared", middle, MUL, middle)
        small_square = calc(f"{distance} squared", distance, MUL, distance)
        return [
            Step(
                f"Both are {distance} away from {middle}",
                f"{left} × {right} = ({middle} − {distance}) × ({middle} + {distance})",
                Fraction((middle - distance) * (middle + distance)),
            ),
            square,
            small_square,
            calc("Subtract", square.value, SUB, small_square.value),
        ]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        middle, distance = rng.randint(2, 9) * 10, rng.randint(1, 9)
        return middle - distance, middle + distance

    @staticmethod
    def _centre(left: int, right: int) -> tuple[int, int] | None:
        """(round middle, distance) when the factors sit symmetrically around a multiple of 10."""
        if left == right or (left + right) % 2:
            return None
        middle, distance = (left + right) // 2, abs(left - right) // 2
        if middle % 10 or middle < 20 or distance > 9:
            return None
        return middle, distance


class SquareEndingInFive(WholeNumberTrick):
    id = "mul-square-5"
    name = "Squares ending in 5"
    summary = "For n5 × n5, multiply n by the next number and write 25 after it."
    operation = MUL
    priority = 90

    def fits(self, left: int, right: int) -> bool:
        return left == right and left % 10 == 5 and 15 <= left <= 95

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        tens = left // 10
        product = calc(f"{tens} times the next number", tens, MUL, tens + 1)
        result = int(product.value) * 100 + 25
        return [
            product,
            Step("Write 25 after it", f"{int(product.value)} | 25 → {result}", Fraction(result)),
        ]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        value = rng.randint(1, 9) * 10 + 5
        return value, value


def _side_by_side(high: int, low: int) -> Step:
    """Write ``high`` and then ``low`` as two digits: 20 | 09 → 2009."""
    result = high * 100 + low
    return Step("Write them side by side", f"{high} | {low:02d} → {result}", Fraction(result))


class UnitsSumToTen(WholeNumberTrick):
    id = "mul-units-sum-10"
    name = "Same tens, units add to 10"
    summary = "43 × 47: tens × next number (4 × 5 = 20), then units × units (3 × 7 = 21) → 2021."
    operation = MUL
    priority = 85

    def fits(self, left: int, right: int) -> bool:
        (tens, unit), (other_tens, other_unit) = digits(left), digits(right)
        return (
            10 <= left <= 99
            and 10 <= right <= 99
            and tens == other_tens
            and unit > 0
            and other_unit > 0
            and unit + other_unit == 10
        )

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        (tens, unit), (_, other_unit) = digits(left), digits(right)
        high = calc(f"{tens} times the next number", tens, MUL, tens + 1)
        low = calc("Multiply the units", unit, MUL, other_unit)
        return [high, low, _side_by_side(int(high.value), int(low.value))]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        tens, unit = rng.randint(1, 9), rng.randint(1, 9)
        return tens * 10 + unit, tens * 10 + 10 - unit


class BaseHundred(WholeNumberTrick):
    id = "mul-base-100"
    name = "Near 100"
    summary = (
        "Both just below (or above) 100: cross-subtract (or add) the differences, "
        "then append their product as two digits."
    )
    operation = MUL
    priority = 85

    def fits(self, left: int, right: int) -> bool:
        below = 91 <= left <= 99 and 91 <= right <= 99
        above = 101 <= left <= 109 and 101 <= right <= 109
        return below or above

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        if left < 100:
            gaps = 100 - left, 100 - right
            high = calc(f"{right} is {gaps[1]} below 100: take that off {left}", left, SUB, gaps[1])
        else:
            gaps = left - 100, right - 100
            high = calc(f"{right} is {gaps[1]} above 100: add that to {left}", left, ADD, gaps[1])
        low = calc("Multiply the two differences from 100", gaps[0], MUL, gaps[1])
        return [high, low, _side_by_side(int(high.value), int(low.value))]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        if rng.random() < 0.7:
            return rng.randint(91, 99), rng.randint(91, 99)
        return rng.randint(101, 109), rng.randint(101, 109)


class TeensTimesTeens(WholeNumberTrick):
    id = "mul-teens"
    name = "Teens × teens"
    summary = "13 × 17: 13 + 7 = 20, times 10 = 200, plus 3 × 7 = 21 → 221."
    operation = MUL
    priority = 60

    def fits(self, left: int, right: int) -> bool:
        return 11 <= left <= 19 and 11 <= right <= 19

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        unit, other_unit = left - 10, right - 10
        total = calc(f"Add {other_unit} (the units of {right}) to {left}", left, ADD, other_unit)
        tens = calc("Times 10", total.value, MUL, 10)
        units = calc("Multiply the units", unit, MUL, other_unit)
        return [total, tens, units, calc("Add them", tens.value, ADD, units.value)]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        return rng.randint(13, 19), rng.randint(13, 19)


class SquareUpAndDown(WholeNumberTrick):
    id = "mul-square-up-down"
    name = "Squaring up and down"
    summary = "a² = (a − d)(a + d) + d²: move to the nearest ten, e.g. 47² = 44 × 50 + 3²."
    operation = MUL
    priority = 50

    def fits(self, left: int, right: int) -> bool:
        return left == right and 11 <= left <= 99 and left % 10 not in (0, 5)

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        unit = left % 10
        distance = unit if unit < 5 else 10 - unit
        down, up = left - distance, left + distance
        product = calc(f"Go {distance} down to {down} and {distance} up to {up}", down, MUL, up)
        square = calc(f"Add {distance} squared", distance, MUL, distance)
        return [product, square, calc("Add them", product.value, ADD, square.value)]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        value = rng.randint(1, 9) * 10 + rng.choice((1, 2, 3, 4, 6, 7, 8, 9))
        return value, value


class CrossMultiplication(WholeNumberTrick):
    id = "mul-cross"
    name = "Vertically and crosswise"
    summary = "Two-digit × two-digit: tens × tens | the two cross products | units × units."
    operation = MUL
    priority = 20

    def fits(self, left: int, right: int) -> bool:
        return 10 <= left <= 99 and 10 <= right <= 99

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        (tens, unit), (other_tens, other_unit) = digits(left), digits(right)
        hundreds = calc("Tens × tens", tens, MUL, other_tens)
        cross = tens * other_unit + unit * other_tens
        units = calc("Units × units", unit, MUL, other_unit)
        total = int(hundreds.value) * 100 + cross * 10 + int(units.value)
        return [
            hundreds,
            Step(
                "Crosswise",
                f"{tens} × {other_unit} + {unit} × {other_tens} = {cross}",
                Fraction(cross),
            ),
            units,
            Step(
                "Combine as hundreds, tens and units",
                f"{int(hundreds.value) * 100} + {cross * 10} + {int(units.value)} = {total}",
                Fraction(total),
            ),
        ]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        return rng.randint(21, 89), rng.randint(21, 89)


class CloseTogether(WholeNumberTrick):
    id = "mul-close-together"
    name = "Close together"
    summary = "Same tens: (z + a)(z + b) = z × (z + a + b) + a × b, e.g. 43 × 48 = 40 × 51 + 3 × 8."
    operation = MUL
    priority = 45

    def fits(self, left: int, right: int) -> bool:
        return (
            20 <= left <= 99
            and 20 <= right <= 99
            and left // 10 == right // 10
            and left % 10 > 0
            and right % 10 > 0
        )

    def steps_for(self, left: int, right: int) -> Sequence[Step]:
        base = left - left % 10
        unit, other_unit = left % 10, right % 10
        total = calc(f"Add {other_unit} (the units of {right}) to {left}", left, ADD, other_unit)
        product = calc(f"Times {base}", base, MUL, total.value)
        units = calc("Multiply the units", unit, MUL, other_unit)
        return [total, product, units, calc("Add them", product.value, ADD, units.value)]

    def example_operands(self, rng: Random) -> tuple[int, int]:
        tens = rng.randint(2, 9) * 10
        return tens + rng.randint(1, 9), tens + rng.randint(1, 9)
