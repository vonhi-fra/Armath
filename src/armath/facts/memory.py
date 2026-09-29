"""How well each fact is known: Leitner boxes, rebuilt by replaying fact sessions.

Nothing is stored separately: the memory is a pure function of the history, so it survives
backups and can never disagree with it.
"""

from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import Enum

from armath.domain import Attempt, SessionKind, SessionRecord
from armath.facts.deck import fact_key

INTERVALS = tuple(timedelta(days=days) for days in (0, 1, 3, 7, 14, 30))
"""How long a fact rests after reaching each box."""
TOP_BOX = len(INTERVALS) - 1
MASTERED_BOX = 3


class Grade(Enum):
    GOOD = "good"
    """Right first time and fast: recalled, not computed."""
    SLOW = "slow"
    MISSED = "missed"
    """A correction, or so slow that it was surely worked out."""


def target_seconds(attempt: Attempt) -> float:
    """Time for instant recall plus typing: longer answers get a little more."""
    return 1.0 + 0.35 * len(str(attempt.problem.answer))


def grade(attempt: Attempt) -> Grade:
    target = target_seconds(attempt)
    if not attempt.is_clean or attempt.elapsed_seconds > 2 * target:
        return Grade.MISSED
    if attempt.elapsed_seconds > target:
        return Grade.SLOW
    return Grade.GOOD


@dataclass(frozen=True)
class FactState:
    box: int
    due: datetime
    reviews: int
    last_seconds: float

    @property
    def mastered(self) -> bool:
        return self.box >= MASTERED_BOX

    def after(self, attempt: Attempt) -> "FactState":
        match grade(attempt):
            case Grade.GOOD:
                box = min(self.box + 1, TOP_BOX)
            case Grade.SLOW:
                box = self.box
            case Grade.MISSED:
                box = 0
        return replace(
            self,
            box=box,
            due=attempt.answered_at + INTERVALS[box],
            reviews=self.reviews + 1,
            last_seconds=attempt.elapsed_seconds,
        )


def first_state(attempt: Attempt) -> FactState:
    return FactState(0, attempt.answered_at, 0, attempt.elapsed_seconds).after(attempt)


class FactMemory:
    def __init__(self, states: dict[str, FactState] | None = None) -> None:
        self._states = dict(states or {})

    @classmethod
    def replay(cls, records: Iterable[SessionRecord]) -> "FactMemory":
        memory = cls()
        for record in records:
            if record.kind is SessionKind.FACTS:
                for attempt in record.attempts:
                    memory.learn(attempt)
        return memory

    def learn(self, attempt: Attempt) -> None:
        key = fact_key(attempt.problem)
        state = self._states.get(key)
        self._states[key] = first_state(attempt) if state is None else state.after(attempt)

    def state(self, key: str) -> FactState | None:
        return self._states.get(key)
