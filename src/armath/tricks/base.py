"""The trick abstraction: a way of solving certain problems in your head."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from random import Random

from armath.domain import Operand, Operation, Problem, Unknown
from armath.tricks.explanation import Explanation, Step


class Trick(ABC):
    """A mental strategy for some problems.

    A trick knows when it applies, how to explain a specific problem step by step and how to
    produce practice problems for itself; it is therefore also a ``ProblemGenerator``.
    Adding a trick means adding a subclass and registering it; nothing else changes.
    Metadata is usually set as class attributes; a trick that works the same way for every
    operation may set it per instance instead.
    """

    id: str
    name: str
    summary: str
    """The rule in one line, e.g. "×5 = ×10, then halve"."""
    operation: Operation
    priority: int
    """When several tricks apply, the highest priority is suggested first."""
    fallback: bool = False
    """A general method that applies to every problem of its kind."""

    @abstractmethod
    def applies_to(self, problem: Problem) -> bool: ...

    @abstractmethod
    def generate(self, rng: Random) -> Problem:
        """A practice problem this trick applies to."""

    def explain(self, problem: Problem) -> Explanation:
        if not self.applies_to(problem):
            raise ValueError(f"{self.name} does not apply to {problem.prompt}")
        return Explanation(self.id, problem, tuple(self._steps(problem)))

    @abstractmethod
    def _steps(self, problem: Problem) -> Sequence[Step]: ...


def whole_operands(problem: Problem) -> tuple[int, int] | None:
    """The operands of a ``a <op> b = ?`` problem if both are non-negative integers."""
    if problem.unknown is not Unknown.RESULT:
        return None
    left, right = problem.left.value, problem.right.value
    if left.denominator != 1 or right.denominator != 1 or left < 0 or right < 0:
        return None
    return int(left), int(right)


class WholeNumberTrick(Trick):
    """A trick for ``a <op> b = ?`` with non-negative integers, as in Zetamac.

    Subclasses only deal with plain ints: :meth:`fits`, :meth:`steps_for` and
    :meth:`example_operands`.
    """

    def applies_to(self, problem: Problem) -> bool:
        operands = whole_operands(problem)
        return problem.operation is self.operation and operands is not None and self.fits(*operands)

    def generate(self, rng: Random) -> Problem:
        left, right = self.example_operands(rng)
        return Problem.create(Operand.integer(left), self.operation, Operand.integer(right))

    def _steps(self, problem: Problem) -> Sequence[Step]:
        operands = whole_operands(problem)
        if operands is None:
            raise ValueError(f"{problem.prompt} is not a whole-number problem")
        return self.steps_for(*operands)

    @abstractmethod
    def fits(self, left: int, right: int) -> bool: ...

    @abstractmethod
    def steps_for(self, left: int, right: int) -> Sequence[Step]: ...

    @abstractmethod
    def example_operands(self, rng: Random) -> tuple[int, int]: ...


def other_factor(left: int, right: int, factor: int) -> int | None:
    """The factor paired with ``factor`` in ``left × right``, if ``factor`` is one of them."""
    if left == factor:
        return right
    if right == factor:
        return left
    return None


def digits(value: int) -> tuple[int, int]:
    """Tens and units of a number below 100."""
    return divmod(value, 10)
