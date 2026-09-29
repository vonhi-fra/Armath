"""What presenters need from the screen; implemented by the DOM adapter and by test fakes."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from armath.analytics import SessionSummary
from armath.ui.settings_form import SettingsForm


class Screen(StrEnum):
    HOME = "home"
    GAME = "game"
    RESULTS = "results"


@dataclass(frozen=True)
class HistoryRow:
    started_at: datetime
    mode: str
    score: int
    first_try_rate: float | None


class Navigator(Protocol):
    def go_to(self, screen: Screen) -> None: ...


class HomeView(Protocol):
    def show_settings(self, form: SettingsForm) -> None: ...

    def show_form_errors(self, errors: Sequence[str]) -> None: ...

    def show_history(self, rows: Sequence[HistoryRow]) -> None: ...


class GameView(Protocol):
    def show_problem(self, prompt: str) -> None: ...

    def clear_answer(self) -> None: ...

    def show_score(self, score: int) -> None: ...

    def show_time(self, text: str) -> None: ...


class ResultsView(Protocol):
    def show_summary(self, summary: SessionSummary) -> None: ...
