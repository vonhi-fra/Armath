"""One presenter per screen; each owns its view and nothing else."""

from collections.abc import Callable, Sequence
from random import Random
from typing import Protocol

from armath.analytics import first_try_rate, summarize
from armath.domain import Problem, SessionRecord
from armath.learning import Drill, TrickLesson, library, review
from armath.modes import Clock, Session, SessionPlan
from armath.persistence import HistoryRepository, SettingsRepository
from armath.settings import PracticeSettings
from armath.tricks import TrickRegistry
from armath.ui.formatting import format_clock
from armath.ui.settings_form import FormError, SettingsForm
from armath.ui.views import GameView, HistoryRow, HomeView, LibraryView, ResultsView

RECENT_SESSIONS = 10
REVIEWED_PROBLEMS = 5


class HomePresenter:
    def __init__(
        self, view: HomeView, history: HistoryRepository, settings: SettingsRepository
    ) -> None:
        self._view = view
        self._history = history
        self._settings = settings

    def show(self) -> None:
        self._view.show_settings(SettingsForm.from_settings(self._settings.load()))
        self._view.show_form_errors([])
        self._view.show_history(recent_history(self._history.all()))

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
        session = self._session
        if session is None:
            return
        if session.is_over:
            self._finish(session)
            return
        if session.answer(text) is None:
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
        self._view.show_steps(None)
        answered = len(session.attempts)
        self._view.show_hint(None if self._coach is None else self._coach.hint(answered))
        self._show_status(session)

    def _show_status(self, session: Session) -> None:
        remaining = session.remaining_time
        limit = session.plan.question_limit
        if remaining is not None:
            self._view.show_status("Time", format_clock(remaining))
        elif limit is not None:
            current = min(len(session.attempts) + 1, limit)
            self._view.show_status("Problem", f"{current} / {limit}")

    def _finish(self, session: Session) -> None:
        self._session = None
        self._on_finished(session.record())


class ResultsPresenter:
    def __init__(self, view: ResultsView, registry: TrickRegistry) -> None:
        self._view = view
        self._registry = registry

    def show(self, record: SessionRecord, drill: Drill | None = None) -> None:
        self._view.show_summary(summarize(record))
        self._view.show_review(review(record, self._registry, REVIEWED_PROBLEMS))
        self._view.show_drill_report(None if drill is None else drill.report(record))


class LibraryPresenter:
    def __init__(self, view: LibraryView, registry: TrickRegistry) -> None:
        self._view = view
        self._registry = registry

    def show(self) -> None:
        self._view.show_library(library(self._registry))
