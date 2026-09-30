"""Percentage tricks (Optiver): percentages are fractions in disguise.

``15%`` is the value 0.15 written as a percentage, so ``15% of 240`` is a multiplication and
``36 ÷ 240 = ?%`` a division whose answer is written as a percentage.
"""

from collections.abc import Sequence
from fractions import Fraction
from random import Random

from armath.domain import NumberStyle, Operand, Operation, Problem, Unknown
from armath.domain.numbers import format_value
from armath.generators.optiver import (
    FRIENDLY_PERCENTS,
    OTHER_PERCENTS,
    PERCENT_BASES,
    SWAP_BASES,
    number,
)
from armath.tricks.base import Trick
from armath.tricks.explanation import Step, calc

MUL, DIV, ADD = Operation.MULTIPLY, Operation.DIVIDE, Operation.ADD

_FRIENDLY = frozenset(Fraction(p) / 100 for p in FRIENDLY_PERCENTS)
"""Friendly percentages as values; each is a simple fraction (12.5% = 0.125 = 1/8)."""


def percent_of(problem: Problem) -> tuple[Fraction, Fraction] | None:
    """(the percentage as a value, the base) for ``p% of n = ?``."""
    if problem.operation is not MUL or problem.unknown is not Unknown.RESULT:
        return None
    percentage, base = problem.left, problem.right
    if percentage.style is not NumberStyle.PERCENT:
        return None
    if base.style in (NumberStyle.PERCENT, NumberStyle.FRACTION) or base.value < 0:
        return None
    return percentage.value, base.value


def _percent(value: Fraction) -> str:
    return str(Operand(value, NumberStyle.PERCENT))


def _percent_problem(percentage: Fraction | int, base: int) -> Problem:
    return Problem.create(Operand.percent(percentage), MUL, number(base))


class PercentAsFraction(Trick):
    id = "pct-fraction"
    name = "Percent as a fraction"
    summary = "25% is 1/4, 12.5% is 1/8, 75% is 3/4: divide (and multiply) instead."
    operation = MUL
    priority = 80

    def applies_to(self, problem: Problem) -> bool:
        split = percent_of(problem)
        return split is not None and split[0] in _FRIENDLY

    def generate(self, rng: Random) -> Problem:
        return _percent_problem(rng.choice(FRIENDLY_PERCENTS), rng.choice(PERCENT_BASES))

    def _steps(self, problem: Problem) -> Sequence[Step]:
        split = percent_of(problem)
        if split is None:
            raise ValueError(f"{problem.prompt} is not a percentage of a number")
        percentage, base = split
        top, bottom = percentage.numerator, percentage.denominator
        steps = [
            Step(
                f"{_percent(percentage)} is {top}/{bottom}",
                f"{_percent(percentage)} = {top}/{bottom}",
                percentage,
            ),
            calc(f"Divide by {bottom}", base, DIV, bottom),
        ]
        if top > 1:
            steps.append(calc(f"Times {top}", steps[-1].value, MUL, top))
        return steps


class PercentSwap(Trick):
    id = "pct-swap"
    name = "Percentage swap"
    summary = "x% of y = y% of x: 24% of 50 is 50% of 24 = 12."
    operation = MUL
    priority = 85

    def applies_to(self, problem: Problem) -> bool:
        split = percent_of(problem)
        if split is None:
            return False
        percentage, base = split
        whole_percentage = (percentage * 100).denominator == 1
        return base in SWAP_BASES and whole_percentage and percentage not in _FRIENDLY

    def generate(self, rng: Random) -> Problem:
        while True:
            problem = _percent_problem(rng.randint(3, 99), rng.choice(SWAP_BASES))
            if self.applies_to(problem):
                return problem

    def _steps(self, problem: Problem) -> Sequence[Step]:
        split = percent_of(problem)
        if split is None:
            raise ValueError(f"{problem.prompt} is not a percentage of a number")
        percentage, base = split
        swapped_percentage, swapped_base = base / 100, percentage * 100
        divisor = int(100 / base)
        return [
            Step(
                "Swap the two numbers",
                f"{_percent(percentage)} of {format_value(base)} = "
                f"{_percent(swapped_percentage)} of {format_value(swapped_base)}",
                swapped_percentage * swapped_base,
            ),
            calc(
                f"{_percent(swapped_percentage)} is 1/{divisor}: divide by {divisor}",
                swapped_base,
                DIV,
                divisor,
            ),
        ]


class PercentFromTens(Trick):
    id = "pct-tens"
    name = "Build it from 10% and 1%"
    summary = "10% of n is n ÷ 10, 5% is half of that, 1% is n ÷ 100: 35% = 3 × 10% + 5%."
    operation = MUL
    priority = 10

    def applies_to(self, problem: Problem) -> bool:
        return percent_of(problem) is not None

    def generate(self, rng: Random) -> Problem:
        return _percent_problem(rng.choice(OTHER_PERCENTS), rng.choice(PERCENT_BASES))

    def _steps(self, problem: Problem) -> Sequence[Step]:
        split = percent_of(problem)
        if split is None:
            raise ValueError(f"{problem.prompt} is not a percentage of a number")
        percentage, base = split
        whole = percentage * 100
        if whole.denominator != 1:  # e.g. 2.5%: just multiply and divide by 100
            product = calc("Multiply", whole, MUL, base)
            return [product, calc("Divide by 100", product.value, DIV, 100)]
        tens, units = divmod(int(whole), 10)
        steps: list[Step] = []
        parts: list[Fraction] = []
        ten = calc(f"10% of {format_value(base)}", base, DIV, 10)
        if tens or units == 5:
            steps.append(ten)
        if tens:
            if tens > 1:
                steps.append(calc(f"{tens * 10}% is {tens} × 10%", ten.value, MUL, tens))
            parts.append(steps[-1].value)
        if units == 5:  # 5% is half of 10%: quicker than 5 × 1%
            steps.append(calc("5% is half of 10%", ten.value, DIV, 2))
            parts.append(steps[-1].value)
        elif units:
            one = calc(f"1% of {format_value(base)}", base, DIV, 100)
            steps.append(one)
            if units > 1:
                steps.append(calc(f"{units}% is {units} × 1%", one.value, MUL, units))
            parts.append(steps[-1].value)
        if len(parts) == 2:
            steps.append(calc("Add the parts", parts[0], ADD, parts[1]))
        return steps


class WhatPercent(Trick):
    id = "pct-what-percent"
    name = "What percent?"
    summary = "Divide the part by the whole, then write the decimal as a percentage."
    operation = DIV
    priority = 80

    def applies_to(self, problem: Problem) -> bool:
        return (
            problem.operation is DIV
            and problem.unknown is Unknown.RESULT
            and problem.result.style is NumberStyle.PERCENT
            and all(
                o.style is not NumberStyle.FRACTION and o.value >= 0
                for o in (problem.left, problem.right)
            )
        )

    def generate(self, rng: Random) -> Problem:
        percentage = Fraction(rng.choice((*FRIENDLY_PERCENTS, *OTHER_PERCENTS))) / 100
        whole = rng.choice(PERCENT_BASES)
        return Problem.create(
            number(percentage * whole), DIV, number(whole), result_style=NumberStyle.PERCENT
        )

    def _steps(self, problem: Problem) -> Sequence[Step]:
        quotient = calc(
            "Divide the part by the whole", problem.left.value, DIV, problem.right.value
        )
        return [
            quotient,
            Step(
                "Write it as a percentage",
                f"{format_value(quotient.value)} = {_percent(quotient.value)}",
                quotient.value,
            ),
        ]


class PercentOfWhat(Trick):
    id = "pct-of-what"
    name = "Find the whole"
    summary = "If 15% is 36, then 1% is 36 ÷ 15 and 100% is 100 times that."
    operation = DIV
    priority = 60

    def applies_to(self, problem: Problem) -> bool:
        return (
            problem.operation is DIV
            and problem.unknown is Unknown.RESULT
            and problem.right.style is NumberStyle.PERCENT
            and problem.right.value > 0
            and problem.left.style is not NumberStyle.FRACTION
            and problem.left.value >= 0
        )

    def generate(self, rng: Random) -> Problem:
        percentage = Fraction(rng.choice(OTHER_PERCENTS)) / 100
        whole = rng.choice(PERCENT_BASES)
        return Problem.create(
            number(percentage * whole), DIV, Operand(percentage, NumberStyle.PERCENT)
        )

    def _steps(self, problem: Problem) -> Sequence[Step]:
        part, percentage = problem.left.value, problem.right.value
        one = calc(
            f"{_percent(percentage)} is {format_value(part)}, so 1% is",
            part,
            DIV,
            percentage * 100,
        )
        return [one, calc("And 100% is", one.value, MUL, 100)]
