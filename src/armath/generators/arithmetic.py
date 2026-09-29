"""General-purpose generators that can be combined into presets."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from random import Random

from armath.domain import Operand, Operation, Problem, Unknown
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


class WeightedGenerator:
    """Picks a generator for each problem with the given relative weights."""

    def __init__(self, weighted: Sequence[tuple[float, ProblemGenerator]]) -> None:
        if not weighted or any(weight <= 0 for weight, _ in weighted):
            raise ValueError("needs at least one generator, all with positive weights")
        self._weights = [weight for weight, _ in weighted]
        self._generators = [generator for _, generator in weighted]

    def generate(self, rng: Random) -> Problem:
        (generator,) = rng.choices(self._generators, weights=self._weights)
        return generator.generate(rng)


class MissingOperandGenerator:
    """Hides an operand instead of the result in a share of another generator's problems.

    ``12 × 7 = ?`` becomes ``12 × ? = 84`` or ``? × 7 = 84``.
    """

    def __init__(self, base: ProblemGenerator, share: float) -> None:
        if not 0 <= share <= 1:
            raise ValueError("share must be between 0 and 1")
        self._base = base
        self._share = share

    def generate(self, rng: Random) -> Problem:
        problem = self._base.generate(rng)
        if rng.random() >= self._share:
            return problem
        unknown = rng.choice((Unknown.LEFT, Unknown.RIGHT))
        try:
            return replace(problem, unknown=unknown)
        except ValueError:  # e.g. 0 × ? = 0 has no unique answer
            return problem


class FilteredGenerator:
    """Keeps drawing from another generator until a problem passes ``accept``."""

    def __init__(
        self, base: ProblemGenerator, accept: Callable[[Problem], bool], max_tries: int = 1000
    ) -> None:
        self._base = base
        self._accept = accept
        self._max_tries = max_tries

    def generate(self, rng: Random) -> Problem:
        for _ in range(self._max_tries):
            problem = self._base.generate(rng)
            if self._accept(problem):
                return problem
        raise RuntimeError(f"no acceptable problem in {self._max_tries} tries")
