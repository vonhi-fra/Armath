"""Scores over time, per mode (only sessions with the same mode are comparable)."""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from armath.domain import SessionKind, SessionRecord


@dataclass(frozen=True)
class ScorePoint:
    started_at: datetime
    score: int


@dataclass(frozen=True)
class ModeProgress:
    mode: str
    points: tuple[ScorePoint, ...]

    @property
    def sessions(self) -> int:
        return len(self.points)

    @property
    def best(self) -> int:
        return max(point.score for point in self.points)

    @property
    def latest(self) -> int:
        return self.points[-1].score


def mode_progress(records: Sequence[SessionRecord]) -> list[ModeProgress]:
    """Practice modes, most played first (ties: most recently played first)."""
    by_mode: dict[str, list[ScorePoint]] = defaultdict(list)
    for record in records:
        if record.kind is SessionKind.PRACTICE:
            by_mode[record.mode].append(ScorePoint(record.started_at, record.score))
    progress = [ModeProgress(mode, tuple(points)) for mode, points in by_mode.items()]
    return sorted(
        progress,
        key=lambda item: (item.sessions, item.points[-1].started_at),
        reverse=True,
    )
