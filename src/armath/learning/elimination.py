"""Ruling out a multiple-choice option without solving it (docs/research.md §6, E1 and E2).

In the Optiver test a wrong answer costs a point, so spotting an impossible option in a second is
worth as much as computing fast. Two checks cover most tempting wrong options:

- magnitude: round every number to one significant figure; an option 10× off is impossible;
- last digit: in whole-number sums, differences and products only the last digits decide the
  last digit of the answer.
"""

import math
from fractions import Fraction

from armath.domain import Operation, Problem, Unknown
from armath.domain.numbers import format_value
from armath.tricks.base import whole_operands
from armath.tricks.inverse import undo

MAGNITUDE_FACTOR = 5
"""An option at least this many times too big or small is caught by estimating."""


def rule_out(problem: Problem, chosen: Fraction) -> str | None:
    """Why ``chosen`` can't be the answer, found without solving; ``None`` if no quick check."""
    answer = problem.answer.value
    if chosen == answer:
        return None
    return _by_magnitude(problem, chosen) or _by_last_digit(problem, chosen)


def _by_magnitude(problem: Problem, chosen: Fraction) -> str | None:
    answer = problem.answer.value
    if answer <= 0 or chosen <= 0:
        return None
    ratio = chosen / answer
    if 1 / MAGNITUDE_FACTOR < ratio < MAGNITUDE_FACTOR:
        return None
    if problem.unknown is Unknown.RESULT:
        x, operation, y = problem.left.value, problem.operation, problem.right.value
    else:
        left, operation, right = undo(problem)
        x, y = left.value, right.value
    rough_x, rough_y = _one_figure(x), _one_figure(y)
    if operation is Operation.DIVIDE and rough_y == 0:
        return None
    estimate = operation.apply(rough_x, rough_y)
    size = "big" if ratio > 1 else "small"
    return (
        f"Estimate: {_show(rough_x)} {operation.symbol} {_show(rough_y)} ≈ {_show(estimate)}, "
        f"so {format_value(chosen)} is about {_times(ratio)} times too {size}."
    )


def _by_last_digit(problem: Problem, chosen: Fraction) -> str | None:
    operands = whole_operands(problem)
    if operands is None or chosen.denominator != 1 or chosen < 0:
        return None
    left, right = operands
    a, b = left % 10, right % 10
    match problem.operation:
        case Operation.ADD:
            digit = (a + b) % 10
        case Operation.SUBTRACT:
            if left < right:
                return None
            digit = (a - b) % 10
        case Operation.MULTIPLY:
            digit = a * b % 10
        case Operation.DIVIDE:
            return None
    if int(chosen) % 10 == digit:
        return None
    return (
        f"Last digits: {a} {problem.operation.symbol} {b} → the answer ends in {digit}, "
        f"but {int(chosen)} ends in {int(chosen) % 10}."
    )


def _one_figure(value: Fraction) -> Fraction:
    """Round to one significant figure: 18 → 20, 0.37 → 0.4, 4488 → 4000."""
    if value == 0:
        return Fraction(0)
    scale = Fraction(10) ** math.floor(math.log10(abs(value)))
    return round(value / scale) * scale


def _times(ratio: Fraction) -> str:
    factor = ratio if ratio >= 1 else 1 / ratio
    return f"{10 ** round(math.log10(factor)):,}"


def _show(value: Fraction) -> str:
    """A rough value, readable: from 10 up whole numbers with separators, below 10 two figures."""
    if value >= 10:
        return f"{round(value):,}"
    return f"{float(value):.2g}"
