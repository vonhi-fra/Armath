"""What presenters need from the screen; implemented by the DOM adapter and by test fakes."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from armath.analytics import KindInsight, ModeProgress, SessionSummary, TrickInsight
from armath.facts import DeckProgress, FactsAdvice, FactsReport
from armath.learning import DrillReport, LibraryEntry, ReviewItem, TrickLesson
from armath.ui.charts import LineChartLayout
from armath.ui.settings_form import SettingsForm


class Screen(StrEnum):
    HOME = "home"
    GAME = "game"
    RESULTS = "results"
    LIBRARY = "library"
    PROGRESS = "progress"
    FACTS = "facts"


@dataclass(frozen=True)
class ProgressReport:
    modes: tuple[str, ...]
    selected: ModeProgress | None
    chart: LineChartLayout | None
    tricks: tuple[TrickInsight, ...]
    kinds: tuple[KindInsight, ...]


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

    def show_recommendations(self, tricks: Sequence[TrickInsight]) -> None: ...

    def show_facts_advice(self, advice: FactsAdvice | None) -> None: ...


class GameView(Protocol):
    def show_problem(self, prompt: str) -> None: ...

    def clear_answer(self) -> None: ...

    def show_score(self, score: int) -> None: ...

    def show_status(self, label: str, value: str) -> None:
        """The progress indicator, e.g. ("Time", "1:23") or ("Problem", "4 / 20")."""
        ...

    def show_hint(self, text: str | None) -> None: ...

    def show_steps(self, lesson: TrickLesson | None) -> None:
        """Reveal a worked solution for the current problem (``None`` hides it)."""
        ...

    def enable_reveal(self, enabled: bool) -> None: ...

    def show_choices(self, labels: Sequence[str] | None) -> None:
        """Multiple-choice options instead of the answer box (``None``: typed answers)."""
        ...

    def show_countdown(self, seconds: int | None) -> None:
        """Seconds until the session begins; ``None`` once it has begun."""
        ...


class ResultsView(Protocol):
    def show_summary(self, summary: SessionSummary) -> None: ...

    def show_review(self, items: Sequence[ReviewItem]) -> None: ...

    def show_drill_report(self, report: DrillReport | None) -> None: ...

    def show_facts_report(self, report: FactsReport | None) -> None: ...


class FactsView(Protocol):
    def show_decks(self, decks: Sequence[DeckProgress]) -> None: ...


class LibraryView(Protocol):
    def show_library(self, entries: Sequence[LibraryEntry]) -> None: ...


class ProgressView(Protocol):
    def show_progress(self, report: ProgressReport) -> None: ...


class BackupView(Protocol):
    def offer_download(self, filename: str, content: str) -> None:
        """Let the user save ``content`` as a file."""
        ...

    def show_backup_message(self, text: str, *, is_error: bool) -> None: ...
