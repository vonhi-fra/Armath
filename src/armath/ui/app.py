"""The application: wires the screens together and routes user actions."""

from collections.abc import Callable
from random import Random

from armath import presets
from armath.domain import SessionRecord
from armath.facts import FactsTraining, deck_by_id
from armath.learning import Drill
from armath.modes import Clock, SessionPlan
from armath.persistence import Backup, HistoryRepository, SettingsRepository
from armath.tricks import TrickRegistry
from armath.ui.presenters import (
    BackupPresenter,
    FactsPresenter,
    GamePresenter,
    HomePresenter,
    LibraryPresenter,
    ProgressPresenter,
    ResultsPresenter,
)
from armath.ui.settings_form import SettingsForm
from armath.ui.views import (
    BackupView,
    FactsView,
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
        backup_view: BackupView,
        facts_view: FactsView,
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
        self._backup = BackupPresenter(backup_view, Backup(history, settings), clock)
        self._facts_screen = FactsPresenter(facts_view, history, clock)
        self._clock = clock
        self._rng = rng
        self._drill: Drill | None = None
        self._facts: FactsTraining | None = None
        self._again: Callable[[], None] = self._start_practice

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

    def open_facts(self) -> None:
        self._game.quit()
        self._facts_screen.show()
        self._navigator.go_to(Screen.FACTS)

    def start_facts(self, deck_id: str) -> None:
        """A spaced-repetition session for one deck; unknown decks are ignored."""
        try:
            deck = deck_by_id(deck_id)
        except KeyError:
            return
        training = FactsTraining(deck, self._history.all(), self._clock.now(), self._rng)
        self._begin(training.plan(), again=lambda: self.start_facts(deck_id), facts=training)

    def export_data(self) -> None:
        self._backup.export()

    def import_data(self, text: str) -> None:
        """Merge a backup file into the data, then refresh the progress screen."""
        self._backup.restore(text)
        self._progress.show()

    def start(self, form: SettingsForm) -> None:
        """Zetamac-style practice with the settings from the home screen."""
        if self._home.submit(form) is not None:
            self._start_practice()

    def start_optiver(self) -> None:
        self._begin(presets.optiver(), again=self.start_optiver)

    def start_drill(self, trick_id: str) -> None:
        """Practise one trick; unknown ids are ignored."""
        try:
            trick = self._registry.get(trick_id)
        except KeyError:
            return
        drill = Drill(trick, self._registry)
        self._begin(drill.plan(), again=lambda: self.start_drill(trick_id), drill=drill)

    def play_again(self) -> None:
        """Repeat the last kind of session (practice with saved settings by default)."""
        self._again()

    def answer(self, text: str) -> None:
        self._game.answer(text)

    def choose(self, index: int) -> None:
        self._game.choose(index)

    def _start_practice(self) -> None:
        self._begin(self._settings.load().plan(), again=self._start_practice)

    def _begin(
        self,
        plan: SessionPlan,
        *,
        again: Callable[[], None],
        drill: Drill | None = None,
        facts: FactsTraining | None = None,
    ) -> None:
        self._drill = drill
        self._facts = facts
        self._again = again
        self._game.start(plan, coach=drill)
        self._navigator.go_to(Screen.GAME)

    def reveal_steps(self) -> None:
        self._game.reveal()

    def tick(self) -> None:
        self._game.tick()

    def _finished(self, record: SessionRecord) -> None:
        self._history.add(record)
        facts = None if self._facts is None else self._facts.report(self._history.all())
        self._results.show(record, self._drill, facts)
        self._navigator.go_to(Screen.RESULTS)
