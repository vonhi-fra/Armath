"""Missing-operand problems (Optiver): undo the operation, then solve the easier problem."""

from collections.abc import Sequence
from dataclasses import replace
from random import Random

from armath.domain import Operand, Operation, Problem, Unknown
from armath.tricks.base import Trick
from armath.tricks.explanation import Step, calc
from armath.tricks.registry import TrickRegistry

_NAMES = {
    Operation.ADD: "Missing number in a sum",
    Operation.SUBTRACT: "Missing number in a difference",
    Operation.MULTIPLY: "Missing factor",
    Operation.DIVIDE: "Missing number in a division",
}
_SUMMARIES = {
    Operation.ADD: "a + ? = c becomes c − a.",
    Operation.SUBTRACT: "a − ? = c becomes a − c, and ? − b = c becomes c + b.",
    Operation.MULTIPLY: "a × ? = c becomes c ÷ a.",
    Operation.DIVIDE: "a ÷ ? = c becomes a ÷ c, and ? ÷ b = c becomes c × b.",
}


def undo(problem: Problem) -> tuple[Operand, Operation, Operand]:
    """The ``x <op> y`` whose result is the hidden operand."""
    left, right, result = problem.left, problem.right, problem.result
    operation = problem.operation
    if problem.unknown is Unknown.RIGHT:
        match operation:
            case Operation.ADD:
                return result, Operation.SUBTRACT, left
            case Operation.SUBTRACT:
                return left, Operation.SUBTRACT, result
            case Operation.MULTIPLY:
                return result, Operation.DIVIDE, left
            case Operation.DIVIDE:
                return left, Operation.DIVIDE, result
    match operation:
        case Operation.ADD:
            return result, Operation.SUBTRACT, right
        case Operation.SUBTRACT:
            return result, Operation.ADD, right
        case Operation.MULTIPLY:
            return result, Operation.DIVIDE, right
        case Operation.DIVIDE:
            return result, Operation.MULTIPLY, right


class MissingOperand(Trick):
    """Rewrites ``a × ? = c`` as ``c ÷ a = ?`` and explains that with the best other trick."""

    fallback = True
    priority = 0

    def __init__(self, operation: Operation, tricks: TrickRegistry) -> None:
        self.operation = operation
        self.id = f"missing-{operation.name.lower()}"
        self.name = _NAMES[operation]
        self.summary = _SUMMARIES[operation]
        self._tricks = tricks

    def applies_to(self, problem: Problem) -> bool:
        return problem.operation is self.operation and problem.unknown is not Unknown.RESULT

    def generate(self, rng: Random) -> Problem:
        small, big = rng.randint(3, 12), rng.randint(13, 99)
        # Subtraction and division are built backwards so every number stays whole.
        left, right = {
            Operation.ADD: (big, small),
            Operation.SUBTRACT: (big + small, small),
            Operation.MULTIPLY: (small, big),
            Operation.DIVIDE: (small * big, small),
        }[self.operation]
        problem = Problem.create(Operand.integer(left), self.operation, Operand.integer(right))
        return replace(problem, unknown=rng.choice((Unknown.LEFT, Unknown.RIGHT)))

    def _steps(self, problem: Problem) -> Sequence[Step]:
        x, operation, y = undo(problem)
        inverse = Problem.create(x, operation, y, result_style=problem.answer.style)
        rewrite = Step(
            "Undo the operation",
            f"{problem.prompt} → {x} {operation.symbol} {y}",
            inverse.answer.value,
        )
        trick = self._tricks.best(inverse)
        if trick is None:
            return [rewrite, calc("Work it out", x.value, operation, y.value)]
        return [rewrite, *trick.explain(inverse).steps]
