"""The application: wires the screens together and routes user actions."""

from random import Random

from armath.domain import SessionRecord
from armath.modes import Clock
from armath.persistence import HistoryRepository, SettingsRepository
from armath.ui.presenters import GamePresenter, HomePresenter, ResultsPresenter
from armath.ui.settings_form import SettingsForm
from armath.ui.views import GameView, HomeView, Navigator, ResultsView, Screen


class App:
    """Every method is a user action or a timer tick; the adapter only forwards events here."""

    def __init__(
        self,
        *,
        navigator: Navigator,
        home_view: HomeView,
        game_view: GameView,
        results_view: ResultsView,
        history: HistoryRepository,
        settings: SettingsRepository,
        clock: Clock,
        rng: Random,
    ) -> None:
        self._navigator = navigator
        self._history = history
        self._settings = settings
        self._home = HomePresenter(home_view, history, settings)
        self._game = GamePresenter(game_view, clock, rng, on_finished=self._finished)
        self._results = ResultsPresenter(results_view)

    def open_home(self) -> None:
        self._game.quit()
        self._home.show()
        self._navigator.go_to(Screen.HOME)

    def start(self, form: SettingsForm) -> None:
        settings = self._home.submit(form)
        if settings is not None:
            self._game.start(settings.plan())
            self._navigator.go_to(Screen.GAME)

    def play_again(self) -> None:
        self._game.start(self._settings.load().plan())
        self._navigator.go_to(Screen.GAME)

    def answer(self, text: str) -> None:
        self._game.answer(text)

    def tick(self) -> None:
        self._game.tick()

    def _finished(self, record: SessionRecord) -> None:
        self._history.add(record)
        self._results.show(record)
        self._navigator.go_to(Screen.RESULTS)
