"""Step-by-step worked solutions."""

from dataclasses import dataclass
from fractions import Fraction

from armath.domain import Operation, Problem
from armath.domain.numbers import format_value


@dataclass(frozen=True)
class Step:
    """One thing to do in your head.

    ``label`` says what to do in words, ``work`` shows it with numbers and ``value`` is what the
    work evaluates to. Build arithmetic steps with :func:`calc` so they are correct by construction.
    """

    label: str
    work: str
    value: Fraction


def calc(label: str, left: int | Fraction, operation: Operation, right: int | Fraction) -> Step:
    """A step that computes ``left <op> right``; its text and value can't disagree."""
    value = operation.apply(Fraction(left), Fraction(right))
    work = f"{format_value(left)} {operation.symbol} {format_value(right)} = {format_value(value)}"
    return Step(label, work, value)


@dataclass(frozen=True)
class Explanation:
    """How a trick solves one problem. Always ends at the problem's answer."""

    trick_id: str
    problem: Problem
    steps: tuple[Step, ...]

    def __post_init__(self) -> None:
        if not self.steps:
            raise ValueError("an explanation needs at least one step")
        if self.result != self.problem.answer.value:
            raise ValueError(
                f"{self.trick_id} explains {self.problem.prompt} as {format_value(self.result)}, "
                f"but the answer is {self.problem.answer}"
            )

    @property
    def result(self) -> Fraction:
        return self.steps[-1].value
