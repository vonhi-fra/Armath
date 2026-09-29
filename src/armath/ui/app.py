"""The application: wires the screens together and routes user actions."""

from random import Random

from armath.domain import SessionRecord
from armath.learning import Drill
from armath.modes import Clock
from armath.persistence import HistoryRepository, SettingsRepository
from armath.tricks import TrickRegistry
from armath.ui.presenters import (
    GamePresenter,
    HomePresenter,
    LibraryPresenter,
    ProgressPresenter,
    ResultsPresenter,
)
from armath.ui.settings_form import SettingsForm
from armath.ui.views import (
    GameView,
    HomeView,
    LibraryView,
    Navigator,
    ProgressView,
    ResultsView,
    Screen,
)


class App:
    """Every method is a user action or a timer tick; the adapter only forwards events here."""

    def __init__(
        self,
        *,
        navigator: Navigator,
        home_view: HomeView,
        game_view: GameView,
        results_view: ResultsView,
        library_view: LibraryView,
        progress_view: ProgressView,
        history: HistoryRepository,
        settings: SettingsRepository,
        registry: TrickRegistry,
        clock: Clock,
        rng: Random,
    ) -> None:
        self._navigator = navigator
        self._history = history
        self._settings = settings
        self._registry = registry
        self._home = HomePresenter(home_view, history, settings, registry)
        self._game = GamePresenter(game_view, clock, rng, on_finished=self._finished)
        self._results = ResultsPresenter(results_view, registry)
        self._library = LibraryPresenter(library_view, registry)
        self._progress = ProgressPresenter(progress_view, history, registry)
        self._drill: Drill | None = None

    def open_home(self) -> None:
        self._game.quit()
        self._home.show()
        self._navigator.go_to(Screen.HOME)

    def open_library(self) -> None:
        self._game.quit()
        self._library.show()
        self._navigator.go_to(Screen.LIBRARY)

    def open_progress(self, mode: str | None = None) -> None:
        """Show progress, for ``mode`` or the most played one; also used to switch modes."""
        self._game.quit()
        self._progress.show(mode)
        self._navigator.go_to(Screen.PROGRESS)

    def start(self, form: SettingsForm) -> None:
        settings = self._home.submit(form)
        if settings is not None:
            self._drill = None
            self._game.start(settings.plan())
            self._navigator.go_to(Screen.GAME)

    def start_drill(self, trick_id: str) -> None:
        """Practise one trick; unknown ids are ignored."""
        try:
            trick = self._registry.get(trick_id)
        except KeyError:
            return
        self._drill = Drill(trick, self._registry)
        self._game.start(self._drill.plan(), coach=self._drill)
        self._navigator.go_to(Screen.GAME)

    def play_again(self) -> None:
        """Repeat the last kind of session: the same drill, or practice with saved settings."""
        if self._drill is not None:
            self.start_drill(self._drill.trick.id)
            return
        self._game.start(self._settings.load().plan())
        self._navigator.go_to(Screen.GAME)

    def answer(self, text: str) -> None:
        self._game.answer(text)

    def reveal_steps(self) -> None:
        self._game.reveal()

    def tick(self) -> None:
        self._game.tick()

    def _finished(self, record: SessionRecord) -> None:
        self._history.add(record)
        self._results.show(record, self._drill)
        self._navigator.go_to(Screen.RESULTS)
