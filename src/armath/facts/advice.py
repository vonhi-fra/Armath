"""Noticing, from practice sessions, that times-table facts need drilling."""

from collections.abc import Sequence
from dataclasses import dataclass

from armath.analytics import recent_practice
from armath.domain import Operation, Problem, SessionRecord
from armath.facts.deck import Deck, times_tables
from armath.facts.memory import Grade, grade
from armath.tricks.base import whole_operands

MIN_SLOW_FACTS = 3
SHOWN_FACTS = 5
TABLES = times_tables(12)


@dataclass(frozen=True)
class FactsAdvice:
    deck_id: str
    deck_name: str
    slow_facts: tuple[str, ...]
    """A few examples, e.g. ``("6 × 7", "7 × 8")``."""
    count: int


def table_fact(problem: Problem, deck: Deck = TABLES) -> str | None:
    """The times-table fact behind a problem: ``7 × 8`` for both 8 × 7 and 56 ÷ 7."""
    operands = whole_operands(problem)
    if operands is None:
        return None
    left, right = operands
    if problem.operation is Operation.MULTIPLY:
        factors = (left, right)
    elif problem.operation is Operation.DIVIDE and right and left % right == 0:
        factors = (right, left // right)
    else:
        return None
    low, high = deck.grid or (2, 12)
    small, big = sorted(factors)
    return f"{small} × {big}" if low <= small and big <= high else None


def advise(records: Sequence[SessionRecord]) -> FactsAdvice | None:
    """Suggest the times-table deck when recent practice shows several slow table facts."""
    slow: dict[str, None] = {}
    for session in recent_practice(records):
        for attempt in session:
            fact = table_fact(attempt.problem)
            if fact is not None and grade(attempt) is not Grade.GOOD:
                slow[fact] = None
    if len(slow) < MIN_SLOW_FACTS:
        return None
    return FactsAdvice(TABLES.id, TABLES.name, tuple(slow)[:SHOWN_FACTS], len(slow))
