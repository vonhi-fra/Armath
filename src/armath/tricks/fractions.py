"""Fraction methods (Optiver): common denominators, multiplying across, flipping to divide."""

from collections.abc import Sequence
from fractions import Fraction
from math import lcm
from random import Random

from armath.domain import NumberStyle, Operation, Problem, Unknown
from armath.domain.numbers import format_value
from armath.generators.optiver import FRACTION_DENOMINATORS, fraction, proper_fraction
from armath.tricks.base import Trick
from armath.tricks.explanation import Step


def fraction_operands(problem: Problem) -> tuple[Fraction, Fraction] | None:
    """Operands of ``a <op> b = ?`` when at least one is written as a fraction."""
    if problem.unknown is not Unknown.RESULT:
        return None
    operands = (problem.left, problem.right)
    if not any(o.style is NumberStyle.FRACTION for o in operands):
        return None
    if any(o.value < 0 for o in operands):
        return None
    return problem.left.value, problem.right.value


def _text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


_METHODS = {
    Operation.ADD: (
        "Common denominator",
        "Rewrite both over the same denominator, add the tops.",
    ),
    Operation.SUBTRACT: (
        "Common denominator",
        "Rewrite both over the same denominator, subtract the tops.",
    ),
    Operation.MULTIPLY: (
        "Multiply across",
        "Multiply the tops and the bottoms, cancelling common factors first.",
    ),
    Operation.DIVIDE: (
        "Flip and multiply",
        "Dividing by a fraction is multiplying by its flip.",
    ),
}


class FractionMethod(Trick):
    """The general method for fractions, one instance per operation."""

    fallback = True
    priority = 0

    def __init__(self, operation: Operation) -> None:
        self.operation = operation
        self.id = f"frac-{operation.name.lower()}"
        self.name, self.summary = _METHODS[operation]

    def applies_to(self, problem: Problem) -> bool:
        return problem.operation is self.operation and fraction_operands(problem) is not None

    def generate(self, rng: Random) -> Problem:
        left, right = proper_fraction(rng), proper_fraction(rng)
        if self.operation is Operation.SUBTRACT:
            left, right = max(left, right), min(left, right)
            if left == right:
                left = Fraction(left.numerator + 1, left.denominator) if left < 1 else left + 1
        if self.operation is Operation.MULTIPLY and rng.random() < 0.5:
            right = Fraction(right.denominator * rng.randint(1, 6))
        if self.operation is Operation.DIVIDE and rng.random() < 0.3:
            left = Fraction(rng.choice(FRACTION_DENOMINATORS))
        return Problem.create(fraction(left), self.operation, fraction(right))

    def _steps(self, problem: Problem) -> Sequence[Step]:
        operands = fraction_operands(problem)
        if operands is None:
            raise ValueError(f"{problem.prompt} has no fractions")
        left, right = operands
        match self.operation:
            case Operation.ADD | Operation.SUBTRACT:
                return self._common_denominator(left, right)
            case Operation.MULTIPLY:
                return self._multiply(left, right, [])
            case Operation.DIVIDE:
                flipped = Fraction(right.denominator, right.numerator)
                flip = Step(
                    f"Flip {_text(right)} and multiply",
                    f"{_text(left)} ÷ {_text(right)} = {_text(left)} × {_text(flipped)}",
                    left / right,
                )
                return self._multiply(left, flipped, [flip])

    def _common_denominator(self, left: Fraction, right: Fraction) -> list[Step]:
        denominator = lcm(left.denominator, right.denominator)
        top_left = left.numerator * (denominator // left.denominator)
        top_right = right.numerator * (denominator // right.denominator)
        symbol = self.operation.symbol
        rewrite = Step(
            f"Rewrite both over {denominator}",
            f"{_text(left)} {symbol} {_text(right)} = "
            f"{top_left}/{denominator} {symbol} {top_right}/{denominator}",
            self.operation.apply(left, right),
        )
        top = self.operation.apply(Fraction(top_left), Fraction(top_right))
        combined = Step(
            "Combine the tops",
            f"{top_left} {symbol} {top_right} = {top}, so {top}/{denominator}",
            Fraction(int(top), denominator),
        )
        return [rewrite, combined, *_simplify(int(top), denominator)]

    @staticmethod
    def _multiply(left: Fraction, right: Fraction, steps: list[Step]) -> list[Step]:
        top = left.numerator * right.numerator
        bottom = left.denominator * right.denominator
        steps.append(
            Step(
                "Multiply the tops and the bottoms",
                f"{left.numerator} × {right.numerator} / {left.denominator} × {right.denominator}"
                f" = {top}/{bottom}",
                Fraction(top, bottom),
            )
        )
        steps.extend(_simplify(top, bottom))
        return steps


def _simplify(top: int, bottom: int) -> list[Step]:
    """A simplifying step, or nothing if ``top/bottom`` is already in lowest terms."""
    value = Fraction(top, bottom)
    if value.numerator == top and value.denominator == bottom:
        return []
    shown = format_value(value) if value.denominator == 1 else _text(value)
    return [Step("Simplify", f"{top}/{bottom} = {shown}", value)]
