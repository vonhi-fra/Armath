"""Multiple-choice options: the answer plus wrong answers that look like real mistakes.

In the Optiver test the options are close to each other, so you can't guess from magnitude alone.
The distractors here mimic common slips: a wrong last digit, a wrong carry, a misplaced decimal
point, or (for fractions) a slightly wrong top or bottom.
"""

from fractions import Fraction
from random import Random
from typing import Protocol

from armath.domain import NumberStyle, Operand, Problem
from armath.domain.numbers import can_write, decimal_places, infer_style

OPTIONS = 4


class ChoiceMaker(Protocol):
    def choices(self, problem: Problem, rng: Random) -> tuple[Operand, ...]:
        """The options to show, in display order; exactly one is the answer."""
        ...


class PlausibleChoices:
    def __init__(self, options: int = OPTIONS) -> None:
        if options < 2:
            raise ValueError("multiple choice needs at least two options")
        self._options = options

    def choices(self, problem: Problem, rng: Random) -> tuple[Operand, ...]:
        answer = problem.answer
        wanted = self._options - 1
        close, slips = _distractors(answer.value, answer.style)
        picked: list[Fraction] = []
        # One decimal-point slip when possible, the rest close to the answer.
        if slips:
            picked.append(rng.choice(slips))
        for value in rng.sample(close, len(close)):
            if len(picked) == wanted:
                break
            if value not in picked:
                picked.append(value)
        step = _unit(answer.value)
        extra = 3
        while len(picked) < wanted:  # rarely needed: pad with further neighbours
            candidate = answer.value + extra * step
            if candidate not in picked:
                picked.append(candidate)
            extra += 1
        options = [answer, *(_operand(value, answer.style) for value in picked)]
        rng.shuffle(options)
        return tuple(options)


def _unit(value: Fraction) -> Fraction:
    """The size of a change in the last written digit (1 for whole numbers, 0.01 for 1.25)."""
    places = decimal_places(value)
    if places is None:
        return Fraction(1, value.denominator)
    return Fraction(1, 10**places)


def _distractors(value: Fraction, style: NumberStyle) -> tuple[list[Fraction], list[Fraction]]:
    """(close mistakes, decimal-point slips), excluding the answer and non-positive values."""
    unit = _unit(value)
    if style is NumberStyle.FRACTION:
        close = [
            value + unit,
            value - unit,
            Fraction(value.numerator + 1, value.denominator),
            Fraction(value.numerator, value.denominator + 1),
        ]
        if value.denominator > 1:
            close.append(Fraction(value.numerator, value.denominator - 1))
        slips = [Fraction(value.denominator, value.numerator)] if value.numerator else []
    else:
        close = [value + k * unit for k in (-2, -1, 1, 2, -10, 10)]
        slips = [value * 10, value / 10]
    return (
        [v for v in dict.fromkeys(close) if _plausible(v, value)],
        [v for v in slips if _plausible(v, value)],
    )


def _plausible(candidate: Fraction, answer: Fraction) -> bool:
    """Different from the answer, and not negative when the answer is positive."""
    return candidate != answer and (candidate > 0 or answer <= 0)


def _operand(value: Fraction, style: NumberStyle) -> Operand:
    return Operand(value, style if can_write(value, style) else infer_style(value))
