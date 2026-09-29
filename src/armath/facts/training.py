"""A fact session: which facts to ask, in what order, and re-asking the ones you miss."""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from random import Random

from armath.domain import Attempt, Problem, SessionKind, SessionRecord
from armath.facts.deck import Deck, Fact, fact_key
from armath.facts.memory import FactMemory, Grade, grade
from armath.modes import CorrectCount, SessionPlan, UntilCorrect

SESSION_SIZE = 30
NEW_PER_SESSION = 8
REQUEUE_GAP = 3
"""A missed fact comes back after this many other problems..."""
MAX_REQUEUES = 2
"""...at most this many times per session."""


def choose_facts(
    deck: Deck,
    memory: FactMemory,
    now: datetime,
    rng: Random,
    size: int = SESSION_SIZE,
    new_limit: int = NEW_PER_SESSION,
) -> list[Fact]:
    """Due facts first (most overdue first), then a few new ones, then early reviews."""
    seen = [(fact, state) for fact in deck.facts if (state := memory.state(fact.key))]
    unseen = [fact for fact in deck.facts if memory.state(fact.key) is None]
    due = [
        fact for fact, state in sorted(seen, key=lambda p: (p[1].due, p[1].box)) if state.due <= now
    ]
    new = unseen[: min(new_limit, len(unseen))]

    picked = due[: max(size - len(new), 0)] + new
    if len(picked) < size:  # review ahead: the least-known facts that aren't due yet
        ahead = [f for f, s in sorted(seen, key=lambda p: (p[1].box, p[1].due)) if f not in picked]
        picked += ahead[: size - len(picked)]
    if len(picked) < size:  # a fresh deck: introduce more new facts
        picked += [fact for fact in unseen if fact not in picked][: size - len(picked)]
    picked = picked[:size]
    rng.shuffle(picked)
    return picked


class FactQueue:
    """The session's problem source; also watches attempts to re-ask missed facts."""

    def __init__(self, facts: list[Fact], deck: Deck) -> None:
        self._upcoming = list(facts)
        self._deck = deck
        self._slots = len(facts)
        self._served = 0
        self._requeued: Counter[str] = Counter()
        self._by_key = {fact.key: fact for fact in deck.facts}

    def generate(self, rng: Random) -> Problem:
        fact = self._upcoming.pop(0) if self._upcoming else rng.choice(self._deck.facts)
        self._served += 1
        return fact.problem(rng)

    def attempted(self, attempt: Attempt) -> None:
        key = fact_key(attempt.problem)
        fact = self._by_key.get(key)
        if fact is None or grade(attempt) is Grade.GOOD or self._requeued[key] >= MAX_REQUEUES:
            return
        self._requeued[key] += 1
        self._upcoming.insert(min(REQUEUE_GAP, len(self._upcoming)), fact)
        # The session length is fixed: whatever falls off the end stays due for next time.
        del self._upcoming[max(self._slots - self._served, 0) :]


@dataclass(frozen=True)
class FactsReport:
    deck_name: str
    total: int
    mastered_before: int
    mastered_after: int
    new_seen: int


class FactsTraining:
    """One fact session for a deck, remembering where the deck stood when it began."""

    def __init__(
        self, deck: Deck, records: list[SessionRecord], now: datetime, rng: Random
    ) -> None:
        self.deck = deck
        self._before = FactMemory.replay(records)
        self._facts = choose_facts(deck, self._before, now, rng)

    def plan(self) -> SessionPlan:
        queue = FactQueue(self._facts, self.deck)
        return SessionPlan(
            generator=queue,
            scoring=CorrectCount(),
            answering=UntilCorrect(),
            question_limit=len(self._facts),
            name=f"Facts: {self.deck.name}",
            kind=SessionKind.FACTS,
            observers=(queue,),
        )

    def report(self, records_after: list[SessionRecord]) -> FactsReport:
        after = FactMemory.replay(records_after)
        return FactsReport(
            deck_name=self.deck.name,
            total=len(self.deck.facts),
            mastered_before=self._mastered(self._before),
            mastered_after=self._mastered(after),
            new_seen=sum(
                1
                for fact in self.deck.facts
                if self._before.state(fact.key) is None and after.state(fact.key) is not None
            ),
        )

    def _mastered(self, memory: FactMemory) -> int:
        return sum(
            1
            for fact in self.deck.facts
            if (state := memory.state(fact.key)) is not None and state.mastered
        )
