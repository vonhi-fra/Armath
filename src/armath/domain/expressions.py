"""Reading a problem typed as text, e.g. ``858 / 11``, ``12 × 7 = ?`` or ``15% of 240``."""

import re
from fractions import Fraction

from armath.domain.numbers import NumberStyle, Operand
from armath.domain.operations import Operation
from armath.domain.problem import Problem

_NUMBER = r"\d+(?:\.\d+)?%?"
_EXPRESSION = re.compile(rf"\s*({_NUMBER})\s*(of|[-+*/xX×÷−])\s*({_NUMBER})\s*(?:=\s*\??\s*)?")
_OPERATIONS = {
    "of": Operation.MULTIPLY,
    "+": Operation.ADD,
    "-": Operation.SUBTRACT,
    "−": Operation.SUBTRACT,
    "*": Operation.MULTIPLY,
    "x": Operation.MULTIPLY,
    "X": Operation.MULTIPLY,
    "×": Operation.MULTIPLY,
    "/": Operation.DIVIDE,
    "÷": Operation.DIVIDE,
}


def parse_problem(text: str) -> Problem:
    """Parse ``a <op> b`` with non-negative integers, decimals or percentages (``15%``);
    raises ``ValueError``."""
    match = _EXPRESSION.fullmatch(text)
    if match is None:
        raise ValueError(f"not a problem: {text!r} (expected something like '12 x 7')")
    left, symbol, right = match.groups()
    return Problem.create(_operand(left), _OPERATIONS[symbol], _operand(right))


def _operand(text: str) -> Operand:
    if text.endswith("%"):
        return Operand.percent(text.removesuffix("%"))
    style = NumberStyle.DECIMAL if "." in text else NumberStyle.INTEGER
    return Operand(Fraction(text), style)
