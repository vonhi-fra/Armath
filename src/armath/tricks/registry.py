"""Looking tricks up and choosing the best one for a problem."""

from collections.abc import Iterable

from armath.domain import Operation, Problem
from armath.tricks.base import Trick
from armath.tricks.explanation import Explanation


class TrickRegistry:
    """An ordered, id-addressable collection of tricks."""

    def __init__(self, tricks: Iterable[Trick]) -> None:
        self._tricks = tuple(tricks)
        self._by_id = {trick.id: trick for trick in self._tricks}
        if len(self._by_id) != len(self._tricks):
            raise ValueError("trick ids must be unique")

    def all(self) -> tuple[Trick, ...]:
        return self._tricks

    def for_operation(self, operation: Operation) -> tuple[Trick, ...]:
        return tuple(trick for trick in self._tricks if trick.operation is operation)

    def get(self, trick_id: str) -> Trick:
        """Raises ``KeyError`` for an unknown id."""
        return self._by_id[trick_id]

    def applicable(self, problem: Problem) -> list[Trick]:
        """Every trick that applies, best first."""
        tricks = [trick for trick in self._tricks if trick.applies_to(problem)]
        return sorted(tricks, key=lambda trick: trick.priority, reverse=True)

    def best(self, problem: Problem) -> Trick | None:
        tricks = self.applicable(problem)
        return tricks[0] if tricks else None

    def explain(self, problem: Problem) -> Explanation | None:
        """The best trick's explanation, or ``None`` if no trick covers the problem."""
        trick = self.best(problem)
        return None if trick is None else trick.explain(problem)
