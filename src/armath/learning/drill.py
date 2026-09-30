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
from armath.domain import Attempt, Operand, Operation, Problem, SessionKind, SessionRecord
from armath.generators import (
    FilteredGenerator,
    MixedGenerator,
    ProblemGenerator,
    ZetamacSettings,
    optiver_generator,
    zetamac_generator,
)
from armath.learning.review import TrickLesson, lesson_for
from armath.modes import CorrectCount, SessionPlan, UntilCorrect
from armath.tricks import Trick, TrickRegistry, WholeNumberTrick
from armath.tricks.base import whole_operands


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


class NearMissGenerator:
    """The trick's own problems with one number nudged until the trick stops applying.

    ``11 × 47`` becomes ``12 × 47``, ``65 × 65`` becomes ``65 × 66``: problems that *look* like
    the trick, so the drill trains spotting when it really applies.
    """

    def __init__(self, trick: Trick, fallback: ProblemGenerator, max_tries: int = 20) -> None:
        self._trick = trick
        self._fallback = fallback
        self._max_tries = max_tries

    def generate(self, rng: Random) -> Problem:
        for _ in range(self._max_tries):
            nudged = _nudge(self._trick.generate(rng), rng)
            if nudged is not None and not self._trick.applies_to(nudged):
                return nudged
        # Some tricks survive small nudges (132 − 87 still crosses a hundred as 132 − 89).
        return self._fallback.generate(rng)


def _nudge(problem: Problem, rng: Random) -> Problem | None:
    """Change one operand by 1 or 2, keeping division exact; ``None`` if that doesn't work."""
    operands = whole_operands(problem)
    if operands is None:
        return None
    left, right = operands
    step = rng.choice((-2, -1, 1, 2))
    if problem.operation is Operation.DIVIDE:
        quotient, divisor = left // right, right + step  # new divisor, same quotient
        left, right = quotient * divisor, divisor
    elif rng.random() < 0.5:
        left += step
    else:
        right += step
    if left < 1 or right < 2 or (problem.operation is Operation.SUBTRACT and left < right):
        return None
    return Problem.create(Operand.integer(left), problem.operation, Operand.integer(right))


def lookalikes_for(trick: Trick) -> ProblemGenerator | None:
    """Problems of the same operation that the trick does *not* apply to.

    For whole-number tricks, half are near misses of the trick's own problems and half ordinary
    Zetamac-style problems; for the others, Optiver-style problems. ``None`` for general methods,
    which apply to everything.
    """
    if trick.fallback:
        return None
    if not isinstance(trick, WholeNumberTrick):
        # Decimal, fraction and percentage tricks: other Optiver problems of the same operation.
        return FilteredGenerator(
            optiver_generator(missing_operand_share=0),
            lambda problem: problem.operation is trick.operation and not trick.applies_to(problem),
        )
    same_operation = zetamac_generator(ZetamacSettings(operations=frozenset({trick.operation})))
    ordinary = FilteredGenerator(same_operation, lambda problem: not trick.applies_to(problem))
    return MixedGenerator([NearMissGenerator(trick, fallback=ordinary), ordinary])


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
            kind=SessionKind.DRILL,
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
