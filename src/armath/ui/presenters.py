"""One presenter per screen; each owns its view and nothing else."""

from collections.abc import Callable, Sequence
from random import Random
from typing import Protocol

from armath.analytics import (
    first_try_rate,
    kind_insights,
    mode_progress,
    recommendations,
    summarize,
    trick_insights,
)
from armath.domain import Attempt, Problem, SessionRecord
from armath.facts import DECKS, FactMemory, FactsReport, deck_progress
from armath.learning import Drill, TrickLesson, library, review
from armath.modes import Clock, Session, SessionPlan
from armath.persistence import (
    Backup,
    BackupError,
    HistoryRepository,
    SettingsRepository,
    backup_filename,
)
from armath.settings import PracticeSettings
from armath.tricks import TrickRegistry
from armath.ui.charts import line_chart
from armath.ui.formatting import format_clock
from armath.ui.settings_form import FormError, SettingsForm
from armath.ui.views import (
    BackupView,
    FactsView,
    GameView,
    HistoryRow,
    HomeView,
    LibraryView,
    ProgressReport,
    ProgressView,
    ResultsView,
)

RECENT_SESSIONS = 10
REVIEWED_PROBLEMS = 5


class HomePresenter:
    def __init__(
        self,
        view: HomeView,
        history: HistoryRepository,
        settings: SettingsRepository,
        registry: TrickRegistry,
    ) -> None:
        self._view = view
        self._history = history
        self._settings = settings
        self._registry = registry

    def show(self) -> None:
        records = self._history.all()
        self._view.show_settings(SettingsForm.from_settings(self._settings.load()))
        self._view.show_form_errors([])
        self._view.show_recommendations(recommendations(trick_insights(records, self._registry)))
        self._view.show_history(recent_history(records))

    def submit(self, form: SettingsForm) -> PracticeSettings | None:
        """Validate and save the form; returns the settings, or ``None`` after showing errors."""
        try:
            settings = form.parse()
        except FormError as error:
            self._view.show_form_errors(error.messages)
            return None
        self._settings.save(settings)
        self._view.show_form_errors([])
        return settings


def recent_history(records: Sequence[SessionRecord]) -> list[HistoryRow]:
    """The latest sessions first."""
    return [
        HistoryRow(record.started_at, record.mode, record.score, first_try_rate(record.attempts))
        for record in reversed(records[-RECENT_SESSIONS:])
    ]


class Coach(Protocol):
    """Help during a session: a hint under the problem and a worked solution on request."""

    def hint(self, answered: int) -> str | None: ...

    def lesson(self, problem: Problem) -> TrickLesson | None: ...


class GamePresenter:
    """Runs one session at a time and reports it through ``on_finished`` when it ends."""

    def __init__(
        self,
        view: GameView,
        clock: Clock,
        rng: Random,
        on_finished: Callable[[SessionRecord], None],
    ) -> None:
        self._view = view
        self._clock = clock
        self._rng = rng
        self._on_finished = on_finished
        self._session: Session | None = None
        self._coach: Coach | None = None

    def start(self, plan: SessionPlan, coach: Coach | None = None) -> None:
        self._session = Session(plan, self._clock, self._rng)
        self._coach = coach
        self._view.enable_reveal(coach is not None)
        self._view.show_score(0)
        self._show_problem(self._session)

    def answer(self, text: str) -> None:
        """Typed input (called on every change)."""
        self._submit(lambda session: session.answer(text))

    def choose(self, index: int) -> None:
        """A multiple-choice option (0-based); ignored if there is no such option."""
        session = self._session
        if session is None or session.choices is None or not 0 <= index < len(session.choices):
            return
        self._submit(lambda session: session.choose(index))

    def _submit(self, respond: Callable[[Session], Attempt | None]) -> None:
        session = self._session
        if session is None:
            return
        if session.is_over:
            self._finish(session)
            return
        if respond(session) is None:
            return
        self._view.show_score(session.score)
        if session.is_over:
            self._finish(session)
        else:
            self._show_problem(session)

    def reveal(self) -> None:
        """Show how to solve the current problem, if a coach is present."""
        if self._session is not None and self._coach is not None:
            self._view.show_steps(self._coach.lesson(self._session.current))

    def tick(self) -> None:
        session = self._session
        if session is None:
            return
        self._show_status(session)
        if session.is_over:
            self._finish(session)

    def quit(self) -> None:
        """Abandon the session without reporting it."""
        self._session = None

    def _show_problem(self, session: Session) -> None:
        self._view.clear_answer()
        self._view.show_problem(session.current.prompt)
        choices = session.choices
        self._view.show_choices(None if choices is None else [str(option) for option in choices])
        self._view.show_steps(None)
        answered = len(session.attempts)
        self._view.show_hint(None if self._coach is None else self._coach.hint(answered))
        self._show_status(session)

    def _show_status(self, session: Session) -> None:
        remaining = session.remaining_time
        limit = session.plan.question_limit
        progress = None
        if limit is not None:
            progress = f"{min(len(session.attempts) + 1, limit)} / {limit}"
        if remaining is not None:
            clock = format_clock(remaining)
            self._view.show_status("Time", clock if progress is None else f"{clock} · {progress}")
        elif progress is not None:
            self._view.show_status("Problem", progress)

    def _finish(self, session: Session) -> None:
        self._session = None
        self._on_finished(session.record())


class ResultsPresenter:
    def __init__(self, view: ResultsView, registry: TrickRegistry) -> None:
        self._view = view
        self._registry = registry

    def show(
        self,
        record: SessionRecord,
        drill: Drill | None = None,
        facts: FactsReport | None = None,
    ) -> None:
        self._view.show_summary(summarize(record))
        self._view.show_review(review(record, self._registry, REVIEWED_PROBLEMS))
        self._view.show_drill_report(None if drill is None else drill.report(record))
        self._view.show_facts_report(facts)


class FactsPresenter:
    def __init__(self, view: FactsView, history: HistoryRepository, clock: Clock) -> None:
        self._view = view
        self._history = history
        self._clock = clock

    def show(self) -> None:
        memory = FactMemory.replay(self._history.all())
        now = self._clock.now()
        self._view.show_decks([deck_progress(deck, memory, now) for deck in DECKS])


class ProgressPresenter:
    def __init__(
        self, view: ProgressView, history: HistoryRepository, registry: TrickRegistry
    ) -> None:
        self._view = view
        self._history = history
        self._registry = registry

    def show(self, mode: str | None = None) -> None:
        """Show progress for ``mode``, or for the most played mode."""
        records = self._history.all()
        modes = mode_progress(records)
        selected = next((item for item in modes if item.mode == mode), modes[0] if modes else None)
        chart = None if selected is None else line_chart([p.score for p in selected.points])
        self._view.show_progress(
            ProgressReport(
                modes=tuple(item.mode for item in modes),
                selected=selected,
                chart=chart,
                tricks=tuple(trick_insights(records, self._registry)),
                kinds=tuple(kind_insights(records)),
            )
        )


class BackupPresenter:
    def __init__(self, view: BackupView, backup: Backup, clock: Clock) -> None:
        self._view = view
        self._backup = backup
        self._clock = clock

    def export(self) -> None:
        now = self._clock.now()
        filename = backup_filename(now)
        self._view.offer_download(filename, self._backup.export(now))
        self._view.show_backup_message(f"Saved your data as {filename}.", is_error=False)

    def restore(self, text: str) -> None:
        try:
            summary = self._backup.restore(text)
        except BackupError as error:
            self._view.show_backup_message(str(error), is_error=True)
            return
        sessions = "session" if summary.added == 1 else "sessions"
        message = f"Restored {summary.added} {sessions}"
        if summary.already_present:
            verb = "was" if summary.already_present == 1 else "were"
            message += f"; {summary.already_present} {verb} already here"
        self._view.show_backup_message(message + ".", is_error=False)


class LibraryPresenter:
    def __init__(self, view: LibraryView, registry: TrickRegistry) -> None:
        self._view = view
        self._registry = registry

    def show(self) -> None:
        self._view.show_library(library(self._registry))
