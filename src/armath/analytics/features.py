"""Grouping problems into comparable types, e.g. "1-digit × 2-digit"."""

from dataclasses import dataclass

from armath.domain import Operation, Problem
from armath.tricks.base import whole_operands

_OPERATION_ORDER = {operation: index for index, operation in enumerate(Operation)}


@dataclass(frozen=True, order=True)
class ProblemKind:
    """Problems of one kind take about the same effort, so their times are comparable."""

    order: tuple[int, str]
    label: str
    operation: Operation

    @property
    def key(self) -> str:
        return f"{self.operation.name}:{self.label}"


def kind_of(problem: Problem) -> ProblemKind | None:
    """The kind of a whole-number ``a <op> b = ?`` problem; ``None`` for anything else."""
    operands = whole_operands(problem)
    if operands is None:
        return None
    left, right = operands
    match problem.operation:
        case Operation.ADD:
            big, small = max(left, right), min(left, right)
            carrying = ", carrying" if left % 10 + right % 10 >= 10 else ""
            label = f"{_digits(big)}-digit + {_digits(small)}-digit{carrying}"
        case Operation.SUBTRACT:
            borrowing = ", borrowing" if left % 10 < right % 10 else ""
            label = f"{_digits(left)}-digit − {_digits(right)}-digit{borrowing}"
        case Operation.MULTIPLY:
            small, big = min(left, right), max(left, right)
            label = f"{_digits(small)}-digit × {_digits(big)}-digit"
        case Operation.DIVIDE:
            label = f"{_digits(left)}-digit ÷ {_digits(right)}-digit"
    operation = problem.operation
    return ProblemKind((_OPERATION_ORDER[operation], label), label, operation)


def _digits(value: int) -> int:
    return len(str(value))
