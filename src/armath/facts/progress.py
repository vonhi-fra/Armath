"""Where each deck stands: how many facts are new, being learned, mastered or due."""

from dataclasses import dataclass
from datetime import datetime

from armath.facts.deck import Deck, Fact
from armath.facts.memory import FactMemory


@dataclass(frozen=True)
class GridCell:
    row: int
    column: int
    box: int | None
    """``None`` for a fact never practised."""
    last_seconds: float | None


@dataclass(frozen=True)
class DeckProgress:
    deck_id: str
    name: str
    description: str
    total: int
    new: int
    learning: int
    mastered: int
    due: int
    grid: tuple[GridCell, ...] = ()
    grid_range: tuple[int, int] | None = None


def deck_progress(deck: Deck, memory: FactMemory, now: datetime) -> DeckProgress:
    states = [memory.state(fact.key) for fact in deck.facts]
    seen = [state for state in states if state is not None]
    mastered = sum(state.mastered for state in seen)
    return DeckProgress(
        deck_id=deck.id,
        name=deck.name,
        description=deck.description,
        total=len(deck.facts),
        new=len(deck.facts) - len(seen),
        learning=len(seen) - mastered,
        mastered=mastered,
        due=sum(state.due <= now for state in seen),
        grid=_grid(deck, memory),
        grid_range=deck.grid,
    )


def _grid(deck: Deck, memory: FactMemory) -> tuple[GridCell, ...]:
    """Every cell of the times table (both halves), for decks drawn as a grid."""
    if deck.grid is None:
        return ()
    low, high = deck.grid
    facts: dict[tuple[int, int], Fact] = {(f.left, f.right): f for f in deck.facts}
    cells = []
    for row in range(low, high + 1):
        for column in range(low, high + 1):
            fact = facts[(min(row, column), max(row, column))]
            state = memory.state(fact.key)
            cells.append(
                GridCell(
                    row,
                    column,
                    None if state is None else state.box,
                    None if state is None else state.last_seconds,
                )
            )
    return tuple(cells)
