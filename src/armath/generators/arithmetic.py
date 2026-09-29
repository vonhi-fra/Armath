"""General-purpose generators that can be combined into presets."""

from collections.abc import Sequence
from dataclasses import dataclass
from random import Random

from armath.domain import Operand, Operation, Problem
from armath.generators.base import ProblemGenerator
from armath.generators.ranges import IntRange


@dataclass(frozen=True)
class RangeGenerator:
    """``left <op> right = ?`` with integer operands drawn from two ranges."""

    operation: Operation
    left: IntRange
    right: IntRange

    def __post_init__(self) -> None:
        if self.operation is Operation.DIVIDE and 0 in self.right:
            raise ValueError("divisor range must not contain 0")

    def generate(self, rng: Random) -> Problem:
        left = Operand.integer(self.left.sample(rng))
        right = Operand.integer(self.right.sample(rng))
        return Problem.create(left, self.operation, right)


_INVERSES = {Operation.ADD: Operation.SUBTRACT, Operation.MULTIPLY: Operation.DIVIDE}


@dataclass(frozen=True)
class InverseGenerator:
    """Runs another generator's problems backwards.

    ``a + b = c`` becomes ``c − a = b`` and ``a × b = c`` becomes ``c ÷ a = b``,
    which is how Zetamac builds subtraction and division.
    """

    base: ProblemGenerator

    def generate(self, rng: Random) -> Problem:
        problem = self.base.generate(rng)
        inverse = _INVERSES.get(problem.operation)
        if inverse is None:
            raise ValueError(f"cannot invert {problem.operation.name} problems")
        return Problem.create(
            problem.result, inverse, problem.left, result_style=problem.right.style
        )


class MixedGenerator:
    """Picks one of several generators uniformly at random for each problem."""

    def __init__(self, generators: Sequence[ProblemGenerator]) -> None:
        if not generators:
            raise ValueError("at least one generator is required")
        self._generators = tuple(generators)

    def generate(self, rng: Random) -> Problem:
        return rng.choice(self._generators).generate(rng)
