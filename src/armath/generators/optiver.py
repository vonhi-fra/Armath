"""Problems in the style of Optiver's 80-in-8 test (docs/research.md §1).

Integers, decimals, fractions and percentages in all four operations, always with "neat" answers
(they are meant to be solvable in your head in ~6 seconds), and a share of missing-operand
questions.
"""

from fractions import Fraction
from random import Random

from armath.domain import NumberStyle, Operand, Operation, Problem
from armath.domain.numbers import decimal_places
from armath.generators.arithmetic import MissingOperandGenerator, WeightedGenerator
from armath.generators.base import ProblemGenerator

MISSING_OPERAND_SHARE = 0.25

FRIENDLY_DECIMALS = tuple(Fraction(1, k) for k in (2, 4, 5, 8, 20))
"""Decimals that are simple unit fractions: 0.5, 0.25, 0.2, 0.125, 0.05."""
DECIMAL_DIVISORS = (
    *FRIENDLY_DECIMALS,
    Fraction(2, 5),
    Fraction(4, 5),
    Fraction(3, 2),
    Fraction(5, 2),
)
FRACTION_DENOMINATORS = (2, 3, 4, 5, 6, 8, 10, 12)


def number(value: Fraction | int) -> Operand:
    """An operand written as an integer when it is whole, otherwise as a decimal."""
    value = Fraction(value)
    style = NumberStyle.INTEGER if value.denominator == 1 else NumberStyle.DECIMAL
    return Operand(value, style)


def fraction(value: Fraction | int) -> Operand:
    value = Fraction(value)
    style = NumberStyle.INTEGER if value.denominator == 1 else NumberStyle.FRACTION
    return Operand(value, style)


def random_decimal(
    rng: Random, low: int = 1, high: int = 99, places: int | None = None
) -> Fraction:
    """A decimal between ``low`` and ``high`` with exactly 1 or 2 decimal places."""
    places = places or rng.choice((1, 2))
    scale = 10**places
    while True:
        value = Fraction(rng.randint(low * scale, high * scale), scale)
        if decimal_places(value) == places:
            return value


def proper_fraction(rng: Random) -> Fraction:
    denominator = rng.choice(FRACTION_DENOMINATORS)
    while True:
        value = Fraction(rng.randint(1, denominator - 1), denominator)
        if value.denominator > 1:
            return value


def _problem(left: Operand, operation: Operation, right: Operand) -> Problem:
    return Problem.create(left, operation, right)


class IntegerSums:
    def generate(self, rng: Random) -> Problem:
        left, right = rng.randint(100, 9999), rng.randint(10, 999)
        if rng.random() < 0.5:
            return _problem(number(left), Operation.ADD, number(right))
        big, small = max(left, right), min(left, right)
        return _problem(number(big), Operation.SUBTRACT, number(small))


class IntegerProducts:
    def generate(self, rng: Random) -> Problem:
        if rng.random() < 0.6:
            left, right = rng.randint(11, 99), rng.randint(11, 99)
        else:
            left, right = rng.randint(3, 9), rng.randint(101, 999)
        return _problem(number(left), Operation.MULTIPLY, number(right))


class IntegerQuotients:
    def generate(self, rng: Random) -> Problem:
        if rng.random() < 0.6:
            divisor, quotient = rng.randint(3, 19), rng.randint(12, 99)
            return _problem(number(divisor * quotient), Operation.DIVIDE, number(divisor))
        # Round numbers such as 63000 ÷ 700.
        divisor, quotient = rng.randint(2, 9), rng.randint(2, 9)
        divisor_zeros = rng.randint(1, 2)
        dividend_zeros = divisor_zeros + rng.randint(0, 2)
        dividend = divisor * quotient * 10**dividend_zeros
        return _problem(number(dividend), Operation.DIVIDE, number(divisor * 10**divisor_zeros))


class DecimalSums:
    def generate(self, rng: Random) -> Problem:
        left, right = random_decimal(rng), random_decimal(rng)
        if rng.random() < 0.5:
            return _problem(number(left), Operation.ADD, number(right))
        big, small = max(left, right), min(left, right)
        if big == small:
            return _problem(number(left), Operation.ADD, number(right))
        return _problem(number(big), Operation.SUBTRACT, number(small))


class DecimalProducts:
    def generate(self, rng: Random) -> Problem:
        roll = rng.random()
        if roll < 0.4:  # 0.25 × 4000
            friendly = rng.choice(FRIENDLY_DECIMALS)
            other = friendly.denominator * rng.randint(2, 30) * 10 ** rng.randint(0, 2)
            left, right = number(friendly), number(other)
        elif roll < 0.7:  # 3.5 × 12
            left, right = number(random_decimal(rng, 1, 20, places=1)), number(rng.randint(2, 12))
        else:  # 0.3 × 0.07
            left = number(Fraction(rng.randint(2, 9), 10 ** rng.randint(1, 2)))
            right = number(Fraction(rng.randint(2, 9), 10 ** rng.randint(1, 2)))
        if rng.random() < 0.5:
            left, right = right, left
        return _problem(left, Operation.MULTIPLY, right)


class DecimalQuotients:
    def generate(self, rng: Random) -> Problem:
        if rng.random() < 0.5:  # 8 ÷ 0.4
            divisor = rng.choice(DECIMAL_DIVISORS)
            quotient = rng.randint(2, 60)
            return _problem(number(divisor * quotient), Operation.DIVIDE, number(divisor))
        # 7.5 ÷ 3
        whole_divisor = rng.randint(2, 9)
        decimal_quotient = random_decimal(rng, 1, 30, places=1)
        return _problem(
            number(decimal_quotient * whole_divisor), Operation.DIVIDE, number(whole_divisor)
        )


class FractionOperations:
    def generate(self, rng: Random) -> Problem:
        left, right = proper_fraction(rng), proper_fraction(rng)
        operation = rng.choice(tuple(Operation))
        if operation is Operation.SUBTRACT and left <= right:
            left, right = right, left
            if left == right:
                operation = Operation.ADD
        if operation is Operation.MULTIPLY and rng.random() < 0.5:
            # A whole number that cancels: 3/4 × 12
            right = Fraction(right.denominator * rng.randint(1, 6))
        return _problem(fraction(left), operation, fraction(right))


FRIENDLY_PERCENTS = (5, 10, Fraction(25, 2), 20, 25, 40, 50, 60, 75, 80)
"""Percentages that are simple fractions: 12.5% = 1/8, 75% = 3/4, …"""
OTHER_PERCENTS = (2, 4, 6, 8, 12, 15, 18, 24, 30, 35, 36, 45, 70)
PERCENT_BASES = (40, 60, 80, 120, 160, 180, 200, 240, 300, 320, 360, 400, 480, 500, 600, 800)
SWAP_BASES = (2, 4, 5, 10, 20, 25, 50)
"""``24% of 50`` is easier as ``50% of 24``."""


class PercentageProblems:
    def generate(self, rng: Random) -> Problem:
        if rng.random() < 0.2:
            percentage: Fraction | int = rng.randint(3, 99)
            base = rng.choice(SWAP_BASES)
        else:
            percentage = rng.choice((*FRIENDLY_PERCENTS, *OTHER_PERCENTS))
            base = rng.choice(PERCENT_BASES)
        return _problem(Operand.percent(percentage), Operation.MULTIPLY, number(base))


def optiver_generator(missing_operand_share: float = MISSING_OPERAND_SHARE) -> ProblemGenerator:
    mix = WeightedGenerator(
        [
            (3, IntegerSums()),
            (3, IntegerProducts()),
            (2, IntegerQuotients()),
            (2, DecimalSums()),
            (3, DecimalProducts()),
            (2, DecimalQuotients()),
            (2, FractionOperations()),
            (2, PercentageProblems()),
        ]
    )
    return MissingOperandGenerator(mix, missing_operand_share)
