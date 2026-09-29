"""Practising one trick: a focused round, then a mixed round with look-alikes.

Research (docs/research.md §4): blocked practice teaches the steps, interleaved practice teaches
*when* a trick applies. So a drill starts with problems that all use the trick, with its rule as
a hint, and ends mixed with similar problems where it may not apply, without hints.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from random import Random
from statistics import fmean

from armath.analytics import first_try_rate
from armath.domain import Attempt, Problem, SessionRecord
from armath.generators import (
    FilteredGenerator,
    ProblemGenerator,
    ZetamacSettings,
    zetamac_generator,
)
from armath.learning.review import TrickLesson, lesson_for
from armath.modes import CorrectCount, SessionPlan, UntilCorrect
from armath.tricks import Trick, TrickRegistry


@dataclass(frozen=True)
class DrillSettings:
    focused: int = 10
    mixed: int = 10
    trick_share: float = 0.5
    """In the mixed round, the chance that a problem is one for the trick."""

    def __post_init__(self) -> None:
        if self.focused < 0 or self.mixed < 0 or self.focused + self.mixed == 0:
            raise ValueError("a drill needs at least one problem")
        if not 0 <= self.trick_share <= 1:
            raise ValueError("trick share must be between 0 and 1")

    @property
    def total(self) -> int:
        return self.focused + self.mixed


class DrillGenerator:
    """Yields the drill's problems in order; stateful, so use one per session."""

    def __init__(
        self,
        trick: Trick,
        lookalikes: ProblemGenerator | None,
        settings: DrillSettings,
    ) -> None:
        self._trick = trick
        self._lookalikes = lookalikes
        self._settings = settings
        self._count = 0

    def generate(self, rng: Random) -> Problem:
        index = self._count
        self._count += 1
        in_focus = index < self._settings.focused
        if in_focus or self._lookalikes is None or rng.random() < self._settings.trick_share:
            return self._trick.generate(rng)
        return self._lookalikes.generate(rng)


def lookalikes_for(trick: Trick) -> ProblemGenerator | None:
    """Zetamac-style problems of the same operation that the trick does *not* apply to.

    ``None`` for general methods, which apply to everything.
    """
    if trick.fallback:
        return None
    same_operation = zetamac_generator(ZetamacSettings(operations=frozenset({trick.operation})))
    return FilteredGenerator(same_operation, lambda problem: not trick.applies_to(problem))


@dataclass(frozen=True)
class DrillReport:
    trick_name: str
    focused_seconds: float | None
    mixed_trick_seconds: float | None
    lookalike_seconds: float | None
    first_try_rate: float | None


class Drill:
    """A drill for one trick. Also the session's coach: it gives hints and explanations."""

    def __init__(
        self, trick: Trick, registry: TrickRegistry, settings: DrillSettings | None = None
    ) -> None:
        self.trick = trick
        self._registry = registry
        self.settings = settings or DrillSettings()

    @property
    def name(self) -> str:
        return f"Drill: {self.trick.name}"

    def plan(self) -> SessionPlan:
        """A fresh plan; call once per session because the generator keeps count."""
        return SessionPlan(
            generator=DrillGenerator(self.trick, lookalikes_for(self.trick), self.settings),
            scoring=CorrectCount(),
            answering=UntilCorrect(),
            question_limit=self.settings.total,
            name=self.name,
        )

    def hint(self, answered: int) -> str | None:
        """What to show under the problem after ``answered`` problems."""
        if answered < self.settings.focused:
            return f"{self.trick.name}: {self.trick.summary}"
        if self.trick.fallback:
            return None
        return f"Mixed round: decide whether “{self.trick.name}” fits before you start."

    def lesson(self, problem: Problem) -> TrickLesson | None:
        """The drilled trick's steps when it fits, otherwise the best trick's."""
        if self.trick.applies_to(problem):
            return TrickLesson.of(self.trick, self.trick.explain(problem))
        return lesson_for(problem, self._registry)

    def report(self, record: SessionRecord) -> DrillReport:
        focused = record.attempts[: self.settings.focused]
        mixed = record.attempts[self.settings.focused :]
        mixed_trick = [a for a in mixed if self.trick.applies_to(a.problem)]
        lookalikes = [a for a in mixed if not self.trick.applies_to(a.problem)]
        return DrillReport(
            trick_name=self.trick.name,
            focused_seconds=_mean_seconds(focused),
            mixed_trick_seconds=_mean_seconds(mixed_trick),
            lookalike_seconds=_mean_seconds(lookalikes),
            first_try_rate=first_try_rate(record.attempts),
        )


def _mean_seconds(attempts: Sequence[Attempt]) -> float | None:
    return fmean(attempt.elapsed_seconds for attempt in attempts) if attempts else None
