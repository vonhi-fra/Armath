"""The user's practice settings, as chosen on the home screen."""

from dataclasses import dataclass, field
from datetime import timedelta

from armath import presets
from armath.generators import ZetamacSettings
from armath.modes import SessionPlan

DURATION_CHOICES = (30, 60, 120, 300, 600)


@dataclass(frozen=True)
class PracticeSettings:
    zetamac: ZetamacSettings = field(default_factory=ZetamacSettings)
    duration_seconds: int = 120

    def __post_init__(self) -> None:
        if self.duration_seconds <= 0:
            raise ValueError("duration must be positive")

    def plan(self) -> SessionPlan:
        return presets.zetamac(self.zetamac, timedelta(seconds=self.duration_seconds))
