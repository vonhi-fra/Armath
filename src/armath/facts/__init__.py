"""Facts mode: recall small facts instantly, trained with spaced repetition."""

from armath.facts.deck import DECKS, Deck, Fact, deck_by_id, fact_key
from armath.facts.memory import FactMemory, FactState, Grade, grade
from armath.facts.progress import DeckProgress, GridCell, deck_progress
from armath.facts.training import FactQueue, FactsReport, FactsTraining, choose_facts

__all__ = [
    "DECKS",
    "Deck",
    "DeckProgress",
    "Fact",
    "FactMemory",
    "FactQueue",
    "FactState",
    "FactsReport",
    "FactsTraining",
    "Grade",
    "GridCell",
    "choose_facts",
    "deck_by_id",
    "deck_progress",
    "fact_key",
    "grade",
]
