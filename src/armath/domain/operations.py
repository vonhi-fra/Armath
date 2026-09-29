"""The four arithmetic operations."""

import operator
from collections.abc import Callable
from enum import Enum
from fractions import Fraction


class Operation(Enum):
    """A binary arithmetic operation; the value is its display symbol."""

    ADD = "+"
    SUBTRACT = "−"
    MULTIPLY = "×"
    DIVIDE = "÷"

    @property
    def symbol(self) -> str:
        return self.value

    def apply(self, left: Fraction, right: Fraction) -> Fraction:
        """Compute ``left <op> right``; dividing by zero raises ``ZeroDivisionError``."""
        return _FUNCTIONS[self](left, right)


_FUNCTIONS: dict[Operation, Callable[[Fraction, Fraction], Fraction]] = {
    Operation.ADD: operator.add,
    Operation.SUBTRACT: operator.sub,
    Operation.MULTIPLY: operator.mul,
    Operation.DIVIDE: operator.truediv,
}
