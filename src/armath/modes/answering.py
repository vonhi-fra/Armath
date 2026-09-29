"""When a response counts as the final answer to the current problem."""

from dataclasses import dataclass
from fractions import Fraction
from typing import Protocol

from armath.domain import Problem


class AnswerPolicy(Protocol):
    def accepts(self, problem: Problem, response: Fraction) -> bool:
        """Whether ``response`` is recorded and the session moves to the next problem."""
        ...


@dataclass(frozen=True)
class UntilCorrect:
    """Only a correct response moves on; checked on every keystroke (Zetamac)."""

    def accepts(self, problem: Problem, response: Fraction) -> bool:
        return problem.is_correct(response)


@dataclass(frozen=True)
class FirstResponse:
    """Any response is final, right or wrong (Optiver 80-in-8)."""

    def accepts(self, problem: Problem, response: Fraction) -> bool:
        return True
