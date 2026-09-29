"""Where the time goes: per problem kind and per trick, from recent practice sessions.

Method (docs/research.md §5):
- Only practice sessions count (drills show hints); the first problem of each session is
  dropped because its time includes reacting to the screen change.
- Your own median time over all these problems is the yardstick. Every second above it on a
  problem is "time lost", credited to the best trick for that problem, so the tricks that would
  save you the most time rise to the top.
"""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from statistics import median

from armath.analytics.features import ProblemKind, kind_of
from armath.analytics.summary import first_try_rate
from armath.domain import Attempt, Operation, SessionKind, SessionRecord
from armath.tricks import TrickRegistry

RECENT_SESSIONS = 20
MIN_PROBLEMS = 4
"""Fewer problems than this say too little to recommend anything."""
MIN_TREND_PROBLEMS = 3


def recent_practice(
    records: Sequence[SessionRecord], sessions: int = RECENT_SESSIONS
) -> list[list[Attempt]]:
    """Attempts of the latest practice sessions, oldest session first, without warm-ups."""
    practice = [record for record in records if record.kind is SessionKind.PRACTICE]
    return [list(record.attempts[1:]) for record in practice[-sessions:]]


@dataclass(frozen=True)
class TrickInsight:
    trick_id: str
    name: str
    summary: str
    is_general: bool
    problems: int
    median_seconds: float
    share_of_time_lost: float
    """Fraction of all seconds above your typical time spent on this trick's problems."""
    earlier_seconds: float | None
    """Median time in the older half of the recent sessions (``None`` if too few problems)."""
    recent_seconds: float | None

    @property
    def is_recommendable(self) -> bool:
        return self.problems >= MIN_PROBLEMS and self.share_of_time_lost > 0


def trick_insights(records: Sequence[SessionRecord], registry: TrickRegistry) -> list[TrickInsight]:
    """Every trick that covered at least one recent problem, most time lost first."""
    sessions = recent_practice(records)
    attempts = [attempt for session in sessions for attempt in session]
    if not attempts:
        return []
    typical = median(attempt.elapsed_seconds for attempt in attempts)
    halfway = len(sessions) // 2

    times: dict[str, list[float]] = defaultdict(list)
    earlier: dict[str, list[float]] = defaultdict(list)
    recent: dict[str, list[float]] = defaultdict(list)
    lost: dict[str, float] = defaultdict(float)
    for index, session in enumerate(sessions):
        for attempt in session:
            trick = registry.best(attempt.problem)
            if trick is None:
                continue
            seconds = attempt.elapsed_seconds
            times[trick.id].append(seconds)
            (earlier if index < halfway else recent)[trick.id].append(seconds)
            lost[trick.id] += max(0.0, seconds - typical)

    total_lost = sum(lost.values())
    insights = []
    for trick_id, trick_times in times.items():
        trick = registry.get(trick_id)
        insights.append(
            TrickInsight(
                trick_id=trick_id,
                name=trick.name,
                summary=trick.summary,
                is_general=trick.fallback,
                problems=len(trick_times),
                median_seconds=median(trick_times),
                share_of_time_lost=lost[trick_id] / total_lost if total_lost else 0.0,
                earlier_seconds=_median_or_none(earlier[trick_id]),
                recent_seconds=_median_or_none(recent[trick_id]),
            )
        )
    return sorted(insights, key=lambda insight: insight.share_of_time_lost, reverse=True)


def recommendations(insights: Sequence[TrickInsight], limit: int = 3) -> list[TrickInsight]:
    """The tricks worth practising next."""
    return [insight for insight in insights if insight.is_recommendable][:limit]


@dataclass(frozen=True)
class KindInsight:
    label: str
    operation: Operation
    problems: int
    median_seconds: float
    first_try_rate: float | None


def kind_insights(records: Sequence[SessionRecord]) -> list[KindInsight]:
    """Recent practice problems grouped by kind, in operation order."""
    groups: dict[ProblemKind, list[Attempt]] = defaultdict(list)
    for session in recent_practice(records):
        for attempt in session:
            kind = kind_of(attempt.problem)
            if kind is not None:
                groups[kind].append(attempt)
    return [
        KindInsight(
            label=kind.label,
            operation=kind.operation,
            problems=len(attempts),
            median_seconds=median(attempt.elapsed_seconds for attempt in attempts),
            first_try_rate=first_try_rate(attempts),
        )
        for kind, attempts in sorted(groups.items())
    ]


def _median_or_none(values: Sequence[float]) -> float | None:
    return median(values) if len(values) >= MIN_TREND_PROBLEMS else None
