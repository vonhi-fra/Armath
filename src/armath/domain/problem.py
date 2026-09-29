"""A single arithmetic problem such as ``12 × 7 = ?`` or ``66 × ? = 138.6``."""

from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from typing import Self

from armath.domain.numbers import NumberStyle, Operand, infer_style
from armath.domain.operations import Operation


class Unknown(StrEnum):
    """Which part of ``left <op> right = result`` the user has to find."""

    LEFT = "left"
    RIGHT = "right"
    RESULT = "result"


PLACEHOLDER = "?"


@dataclass(frozen=True)
class Problem:
    """The equation ``left <op> right = result`` with one part hidden.

    Always valid: the equation holds and the hidden part has exactly one solution.
    Build it with :meth:`create`, which computes the result.
    """

    left: Operand
    operation: Operation
    right: Operand
    result: Operand
    unknown: Unknown = Unknown.RESULT

    def __post_init__(self) -> None:
        if self.operation is Operation.DIVIDE and self.right.value == 0:
            raise ValueError("division by zero")
        if self.operation.apply(self.left.value, self.right.value) != self.result.value:
            raise ValueError(f"equation does not hold: {self.equation}")
        if not self._has_unique_answer():
            raise ValueError(f"the unknown is not uniquely determined: {self.prompt}")

    @classmethod
    def create(
        cls,
        left: Operand,
        operation: Operation,
        right: Operand,
        *,
        unknown: Unknown = Unknown.RESULT,
        result_style: NumberStyle | None = None,
    ) -> Self:
        """Build a problem, computing the result and (unless given) its display style."""
        if operation is Operation.DIVIDE and right.value == 0:
            raise ValueError("division by zero")
        value = operation.apply(left.value, right.value)
        if result_style is None:
            result_style = infer_style(value, left.style, right.style)
        return cls(left, operation, right, Operand(value, result_style), unknown)

    @property
    def answer(self) -> Operand:
        """The hidden part of the equation."""
        return self._part(self.unknown)

    def is_correct(self, response: Fraction) -> bool:
        return response == self.answer.value

    @property
    def prompt(self) -> str:
        """The problem as shown to the user, e.g. ``66 × ? = 138.6``."""
        left = self._shown(Unknown.LEFT)
        right = self._shown(Unknown.RIGHT)
        result = self._shown(Unknown.RESULT)
        return f"{left} {self.operation.symbol} {right} = {result}"

    @property
    def equation(self) -> str:
        """The problem with every part shown, e.g. ``66 × 2.1 = 138.6``."""
        return f"{self.left} {self.operation.symbol} {self.right} = {self.result}"

    def _part(self, part: Unknown) -> Operand:
        match part:
            case Unknown.LEFT:
                return self.left
            case Unknown.RIGHT:
                return self.right
            case Unknown.RESULT:
                return self.result

    def _shown(self, part: Unknown) -> str:
        return PLACEHOLDER if part is self.unknown else str(self._part(part))

    def _has_unique_answer(self) -> bool:
        match self.operation, self.unknown:
            case Operation.MULTIPLY, Unknown.LEFT:
                return self.right.value != 0
            case Operation.MULTIPLY, Unknown.RIGHT:
                return self.left.value != 0
            case Operation.DIVIDE, Unknown.RIGHT:
                return self.result.value != 0
            case _:
                return True
