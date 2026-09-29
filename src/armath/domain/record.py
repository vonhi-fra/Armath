"""A finished practice session, as kept in the history."""

from dataclasses import dataclass
from datetime import datetime

from armath.domain.attempt import Attempt


@dataclass(frozen=True)
class SessionRecord:
    """What happened in one session: its mode, when it started, its score and every attempt."""

    mode: str
    started_at: datetime
    score: int
    attempts: tuple[Attempt, ...]

    def __post_init__(self) -> None:
        if self.started_at.tzinfo is None:
            raise ValueError("started_at must be timezone-aware")
