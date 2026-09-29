"""One presenter per screen; each owns its view and nothing else."""

from collections.abc import Callable, Sequence
from random import Random

from armath.analytics import summarize
from armath.domain import SessionRecord
from armath.modes import Clock, Session, SessionPlan
from armath.persistence import HistoryRepository, SettingsRepository
from armath.settings import PracticeSettings
from armath.ui.formatting import format_clock
from armath.ui.settings_form import FormError, SettingsForm
from armath.ui.views import GameView, HistoryRow, HomeView, ResultsView

RECENT_SESSIONS = 10


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
    rows = []
    for record in reversed(records[-RECENT_SESSIONS:]):
        answered = len(record.attempts)
        correct = sum(attempt.is_correct for attempt in record.attempts)
        accuracy = correct / answered if answered else None
        rows.append(HistoryRow(record.started_at, record.mode, record.score, accuracy))
    return rows


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

    @property
    def is_playing(self) -> bool:
        return self._session is not None

    def start(self, plan: SessionPlan) -> None:
        self._session = Session(plan, self._clock, self._rng)
        self._view.clear_answer()
        self._view.show_problem(self._session.current.prompt)
        self._view.show_score(0)
        self._show_time(self._session)

    def answer(self, text: str) -> None:
        session = self._session
        if session is None:
            return
        if session.is_over:
            self._finish(session)
            return
        if session.answer(text) is not None:
            self._view.clear_answer()
            self._view.show_problem(session.current.prompt)
            self._view.show_score(session.score)

    def tick(self) -> None:
        session = self._session
        if session is None:
            return
        self._show_time(session)
        if session.is_over:
            self._finish(session)

    def quit(self) -> None:
        """Abandon the session without reporting it."""
        self._session = None

    def _show_time(self, session: Session) -> None:
        remaining = session.remaining_time
        if remaining is not None:
            self._view.show_time(format_clock(remaining))

    def _finish(self, session: Session) -> None:
        self._session = None
        self._on_finished(session.record())


class ResultsPresenter:
    def __init__(self, view: ResultsView) -> None:
        self._view = view

    def show(self, record: SessionRecord) -> None:
        self._view.show_summary(summarize(record))
