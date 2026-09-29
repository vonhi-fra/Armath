"""Decimal tricks (Optiver): work with whole numbers; spot decimals that are simple fractions."""

from collections.abc import Sequence
from fractions import Fraction
from random import Random

from armath.domain import NumberStyle, Operation, Problem, Unknown
from armath.domain.numbers import decimal_places, format_value
from armath.generators.optiver import (
    DECIMAL_DIVISORS,
    FRIENDLY_DECIMALS,
    number,
    random_decimal,
)
from armath.tricks.base import Trick
from armath.tricks.explanation import Step, calc

_METHODS = {
    Operation.ADD: (
        "Line up the decimal points",
        "Scale both to whole numbers, add, then scale back.",
    ),
    Operation.SUBTRACT: (
        "Line up the decimal points",
        "Scale both to whole numbers, subtract, then scale back.",
    ),
    Operation.MULTIPLY: (
        "Multiply as whole numbers",
        "Ignore the decimal points, multiply, then put back as many decimal places "
        "as the factors had.",
    ),
    Operation.DIVIDE: (
        "Shift the decimal point",
        "Move the decimal point the same number of places in both until the divisor is whole.",
    ),
}


def decimal_operands(problem: Problem) -> tuple[Fraction, Fraction] | None:
    """Operands of ``a <op> b = ?`` when at least one is a decimal and none is a fraction."""
    if problem.unknown is not Unknown.RESULT:
        return None
    operands = (problem.left, problem.right)
    if any(o.style is NumberStyle.FRACTION or o.value < 0 for o in operands):
        return None
    if all(o.value.denominator == 1 for o in operands):
        return None
    return problem.left.value, problem.right.value


def _inexact_whole_division(problem: Problem) -> bool:
    """Whole numbers whose quotient is not whole, such as 39 ÷ 2 = 19.5."""
    if problem.operation is not Operation.DIVIDE or problem.unknown is not Unknown.RESULT:
        return False
    left, right = problem.left, problem.right
    whole = all(
        o.value.denominator == 1 and o.value >= 0 and o.style is not NumberStyle.FRACTION
        for o in (left, right)
    )
    return whole and right.value > 0 and left.value % right.value != 0


def _long_division(dividend: int, divisor: int) -> list[Step]:
    whole, remainder = divmod(dividend, divisor)
    rest = calc(f"The remainder {remainder} as a decimal", remainder, Operation.DIVIDE, divisor)
    return [
        Step(
            "Divide as far as whole numbers go",
            f"{dividend} ÷ {divisor} = {whole} remainder {remainder}",
            Fraction(whole),
        ),
        rest,
        calc("Add them", whole, Operation.ADD, rest.value),
    ]


def _places(value: Fraction) -> int:
    return decimal_places(value) or 0


class DecimalMethod(Trick):
    """The general method for decimals: scale to whole numbers, compute, scale back."""

    fallback = True
    priority = 0

    def __init__(self, operation: Operation) -> None:
        self.operation = operation
        self.id = f"dec-{operation.name.lower()}"
        self.name, self.summary = _METHODS[operation]

    def applies_to(self, problem: Problem) -> bool:
        if problem.operation is not self.operation:
            return False
        return decimal_operands(problem) is not None or _inexact_whole_division(problem)

    def generate(self, rng: Random) -> Problem:
        match self.operation:
            case Operation.ADD | Operation.SUBTRACT:
                left, right = sorted((random_decimal(rng), random_decimal(rng)), reverse=True)
                if left == right:
                    left += Fraction(1, 10)
            case Operation.MULTIPLY:
                left, right = random_decimal(rng, 1, 20, places=1), Fraction(rng.randint(2, 12))
            case Operation.DIVIDE:
                right = rng.choice(DECIMAL_DIVISORS[5:])
                left = right * rng.randint(2, 40)
        return Problem.create(number(left), self.operation, number(right))

    def _steps(self, problem: Problem) -> Sequence[Step]:
        if _inexact_whole_division(problem):
            return _long_division(int(problem.left.value), int(problem.right.value))
        operands = decimal_operands(problem)
        if operands is None:
            raise ValueError(f"{problem.prompt} has no decimals")
        left, right = operands
        symbol = self.operation.symbol
        if self.operation is Operation.MULTIPLY:
            left_places, right_places = _places(left), _places(right)
            a, b = left * 10**left_places, right * 10**right_places
            product = calc("Multiply the whole numbers", a, Operation.MULTIPLY, b)
            places = left_places + right_places
            return [
                Step(
                    "Ignore the decimal points",
                    f"{format_value(left)} × {format_value(right)} → {a} × {b}",
                    a * b,
                ),
                product,
                calc(
                    f"Put back {places} decimal place{'s' if places > 1 else ''}",
                    product.value,
                    Operation.DIVIDE,
                    10**places,
                ),
            ]
        places = max(_places(left), _places(right))
        scale = 10**places
        a, b = left * scale, right * scale
        scaled = Step(
            f"Move the decimal point {places} place{'s' if places > 1 else ''} in both",
            f"{format_value(left)} {symbol} {format_value(right)} → {a} {symbol} {b}",
            self.operation.apply(a, b),
        )
        whole = calc("Work with whole numbers", a, self.operation, b)
        if self.operation is Operation.DIVIDE:  # the quotient doesn't change when scaling both
            return [scaled, whole]
        return [scaled, whole, calc("Move the point back", whole.value, Operation.DIVIDE, scale)]


class FriendlyDecimal(Trick):
    """×0.25 is ÷4 and ÷0.25 is ×4 (likewise 0.5, 0.2, 0.125, 0.05)."""

    priority = 75

    def __init__(self, operation: Operation) -> None:
        if operation not in (Operation.MULTIPLY, Operation.DIVIDE):
            raise ValueError("only for multiplication and division")
        self.operation = operation
        if operation is Operation.MULTIPLY:
            self.id, self.name = "dec-friendly-times", "Decimal as a fraction"
            self.summary = (
                "0.5, 0.25, 0.2, 0.125 and 0.05 are 1/2, 1/4, 1/5, 1/8, 1/20: divide instead."
            )
        else:
            self.id, self.name = "dec-friendly-divide", "Dividing by a decimal fraction"
            self.summary = (
                "Dividing by 0.5, 0.25, 0.2, 0.125 or 0.05 is multiplying by 2, 4, 5, 8 or 20."
            )

    def applies_to(self, problem: Problem) -> bool:
        return problem.operation is self.operation and self._split(problem) is not None

    def generate(self, rng: Random) -> Problem:
        friendly = rng.choice(FRIENDLY_DECIMALS)
        if self.operation is Operation.MULTIPLY:
            other = friendly.denominator * rng.randint(2, 30) * 10 ** rng.randint(0, 2)
            return Problem.create(number(friendly), Operation.MULTIPLY, number(other))
        return Problem.create(number(rng.randint(2, 40)), Operation.DIVIDE, number(friendly))

    def _split(self, problem: Problem) -> tuple[Fraction, Fraction] | None:
        """(the other number, the friendly decimal)."""
        operands = decimal_operands(problem)
        if operands is None:
            return None
        left, right = operands
        if right in FRIENDLY_DECIMALS:
            return left, right
        if self.operation is Operation.MULTIPLY and left in FRIENDLY_DECIMALS:
            return right, left
        return None

    def _steps(self, problem: Problem) -> Sequence[Step]:
        split = self._split(problem)
        if split is None:
            raise ValueError(f"{problem.prompt} has no friendly decimal")
        other, friendly = split
        k = friendly.denominator
        as_fraction = Step(
            f"{format_value(friendly)} is 1/{k}", f"{format_value(friendly)} = 1/{k}", friendly
        )
        if self.operation is Operation.MULTIPLY:
            return [as_fraction, calc(f"So divide by {k}", other, Operation.DIVIDE, k)]
        return [as_fraction, calc(f"So multiply by {k}", other, Operation.MULTIPLY, k)]
