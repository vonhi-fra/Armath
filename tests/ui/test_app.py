from collections.abc import Sequence
from dataclasses import replace
from datetime import timedelta
from random import Random

import pytest
from factories import START, attempt, record

from armath.analytics import SessionSummary
from armath.modes import ManualClock
from armath.persistence import MemoryStore, StoredHistory, StoredSettings
from armath.settings import PracticeSettings
from armath.ui import App, HistoryRow, RangeFields, Screen, SettingsForm
from armath.ui.formatting import format_clock


class FakeScreen:
    """Implements every view protocol and the navigator, remembering what was shown."""

    def __init__(self) -> None:
        self.screen: Screen | None = None
        self.form: SettingsForm | None = None
        self.errors: list[str] = []
        self.history: list[HistoryRow] = []
        self.problem = ""
        self.score = 0
        self.time = ""
        self.summary: SessionSummary | None = None
        self.cleared = 0

    def go_to(self, screen: Screen) -> None:
        self.screen = screen

    def show_settings(self, form: SettingsForm) -> None:
        self.form = form

    def show_form_errors(self, errors: Sequence[str]) -> None:
        self.errors = list(errors)

    def show_history(self, rows: Sequence[HistoryRow]) -> None:
        self.history = list(rows)

    def show_problem(self, prompt: str) -> None:
        self.problem = prompt

    def clear_answer(self) -> None:
        self.cleared += 1

    def show_score(self, score: int) -> None:
        self.score = score

    def show_time(self, text: str) -> None:
        self.time = text

    def show_summary(self, summary: SessionSummary) -> None:
        self.summary = summary


class Harness:
    def __init__(self) -> None:
        self.screen = FakeScreen()
        self.clock = ManualClock(START)
        self.store = MemoryStore()
        self.app = App(
            navigator=self.screen,
            home_view=self.screen,
            game_view=self.screen,
            results_view=self.screen,
            history=StoredHistory(self.store),
            settings=StoredSettings(self.store),
            clock=self.clock,
            rng=Random(0),
        )

    def current_answer(self) -> str:
        a, symbol, b, _equals, _placeholder = self.screen.problem.split(" ")
        x, y = int(a), int(b)
        results = {"+": x + y, "−": x - y, "×": x * y, "÷": x // y}
        return str(results[symbol])

    def start(self, seconds: int = 30) -> None:
        self.app.open_home()
        assert self.screen.form is not None
        self.app.start(replace(self.screen.form, duration_seconds=str(seconds)))


@pytest.fixture
def harness() -> Harness:
    return Harness()


def test_home_shows_default_settings_and_empty_history(harness: Harness) -> None:
    harness.app.open_home()

    assert harness.screen.screen is Screen.HOME
    assert harness.screen.form == SettingsForm.from_settings(PracticeSettings())
    assert harness.screen.history == []


def test_invalid_form_stays_home_with_errors(harness: Harness) -> None:
    harness.app.open_home()
    assert harness.screen.form is not None

    harness.app.start(replace(harness.screen.form, addition_left=RangeFields("x", "5")))

    assert harness.screen.screen is Screen.HOME
    assert harness.screen.errors == ["Addition, left (from): 'x' is not a whole number."]


def test_starting_shows_first_problem_and_full_time(harness: Harness) -> None:
    harness.start(seconds=30)

    assert harness.screen.screen is Screen.GAME
    assert harness.screen.problem.endswith("= ?")
    assert harness.screen.time == "0:30"
    assert harness.screen.score == 0


def test_correct_answer_advances_and_scores(harness: Harness) -> None:
    harness.start()
    cleared_before = harness.screen.cleared

    harness.app.answer(harness.current_answer())

    assert harness.screen.score == 1
    assert harness.screen.cleared == cleared_before + 1


def test_wrong_answer_keeps_problem(harness: Harness) -> None:
    harness.start()
    first = harness.screen.problem

    harness.app.answer("-999999")

    assert harness.screen.problem == first
    assert harness.screen.score == 0


def test_time_running_out_saves_session_and_shows_results(harness: Harness) -> None:
    harness.start(seconds=30)
    harness.clock.advance(3)
    harness.app.answer(harness.current_answer())

    harness.clock.advance(12.5)
    harness.app.tick()
    assert harness.screen.time == "0:15"

    harness.clock.advance(15)
    harness.app.tick()

    assert harness.screen.screen is Screen.RESULTS
    assert harness.screen.summary is not None
    assert harness.screen.summary.score == 1
    assert harness.screen.summary.mode == "Zetamac 30s"
    assert len(StoredHistory(harness.store).all()) == 1


def test_answer_after_time_is_up_finishes_instead_of_crashing(harness: Harness) -> None:
    harness.start(seconds=30)
    harness.clock.advance(31)

    harness.app.answer("1")

    assert harness.screen.screen is Screen.RESULTS


def test_going_home_mid_game_discards_session(harness: Harness) -> None:
    harness.start()
    harness.app.answer(harness.current_answer())

    harness.app.open_home()
    harness.clock.advance(1000)
    harness.app.tick()

    assert harness.screen.screen is Screen.HOME
    assert StoredHistory(harness.store).all() == []


def test_play_again_reuses_saved_settings(harness: Harness) -> None:
    harness.start(seconds=60)
    harness.clock.advance(61)
    harness.app.tick()

    harness.app.play_again()

    assert harness.screen.screen is Screen.GAME
    assert harness.screen.time == "1:00"


def test_home_lists_recent_sessions_newest_first(harness: Harness) -> None:
    history = StoredHistory(harness.store)
    history.add(record(attempt(), mode="old"))
    history.add(record(attempt(), attempt(correct=False), mode="new"))

    harness.app.open_home()

    assert [(row.mode, row.accuracy) for row in harness.screen.history] == [
        ("new", 0.5),
        ("old", 1.0),
    ]


@pytest.mark.parametrize(
    ("seconds", "text"),
    [(120, "2:00"), (59.2, "1:00"), (0.3, "0:01"), (0, "0:00"), (-1, "0:00")],
)
def test_format_clock(seconds: float, text: str) -> None:
    assert format_clock(timedelta(seconds=seconds)) == text
