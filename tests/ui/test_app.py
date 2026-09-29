from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import timedelta
from fractions import Fraction
from operator import add, mul, sub, truediv
from random import Random

import pytest
from factories import START, attempt, problem, record

from armath.analytics import SessionSummary, TrickInsight
from armath.domain import Operation, SessionKind
from armath.facts import DeckProgress, FactsReport
from armath.learning import DrillReport, LibraryEntry, ReviewItem, TrickLesson
from armath.modes import ManualClock
from armath.persistence import MemoryStore, StoredHistory, StoredSettings
from armath.settings import PracticeSettings
from armath.tricks import default_registry
from armath.ui import App, HistoryRow, ProgressReport, RangeFields, Screen, SettingsForm
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
        self.status_label = ""
        self.summary: SessionSummary | None = None
        self.cleared = 0
        self.hint: str | None = None
        self.steps: TrickLesson | None = None
        self.reveal_enabled = False
        self.review: list[ReviewItem] = []
        self.drill_report: DrillReport | None = None
        self.library: list[LibraryEntry] = []
        self.recommended: list[TrickInsight] = []
        self.choices: list[str] | None = None
        self.download: tuple[str, str] | None = None
        self.decks: list[DeckProgress] = []
        self.facts_report: FactsReport | None = None
        self.backup_message: tuple[str, bool] | None = None
        self.progress: ProgressReport | None = None

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

    def show_status(self, label: str, value: str) -> None:
        self.status_label, self.time = label, value

    def show_hint(self, text: str | None) -> None:
        self.hint = text

    def show_steps(self, lesson: TrickLesson | None) -> None:
        self.steps = lesson

    def enable_reveal(self, enabled: bool) -> None:
        self.reveal_enabled = enabled

    def show_choices(self, labels: Sequence[str] | None) -> None:
        self.choices = None if labels is None else list(labels)

    def show_summary(self, summary: SessionSummary) -> None:
        self.summary = summary

    def show_review(self, items: Sequence[ReviewItem]) -> None:
        self.review = list(items)

    def show_drill_report(self, report: DrillReport | None) -> None:
        self.drill_report = report

    def show_library(self, entries: Sequence[LibraryEntry]) -> None:
        self.library = list(entries)

    def show_recommendations(self, tricks: Sequence[TrickInsight]) -> None:
        self.recommended = list(tricks)

    def show_progress(self, report: ProgressReport) -> None:
        self.progress = report

    def show_decks(self, decks: Sequence[DeckProgress]) -> None:
        self.decks = list(decks)

    def show_facts_report(self, report: FactsReport | None) -> None:
        self.facts_report = report

    def offer_download(self, filename: str, content: str) -> None:
        self.download = (filename, content)

    def show_backup_message(self, text: str, *, is_error: bool) -> None:
        self.backup_message = (text, is_error)


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
            library_view=self.screen,
            progress_view=self.screen,
            backup_view=self.screen,
            facts_view=self.screen,
            history=StoredHistory(self.store),
            settings=StoredSettings(self.store),
            registry=default_registry(),
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

    assert [(row.mode, row.first_try_rate) for row in harness.screen.history] == [
        ("new", 0.5),
        ("old", 1.0),
    ]


def test_results_review_the_slowest_problems_with_tricks(harness: Harness) -> None:
    harness.start(seconds=30)
    for seconds in (1, 4, 2):
        harness.clock.advance(seconds)
        harness.app.answer(harness.current_answer())
    harness.clock.advance(30)
    harness.app.tick()

    review = harness.screen.review
    assert [item.seconds for item in review] == [4, 2, 1]
    assert all(item.lesson is not None for item in review)
    assert harness.screen.drill_report is None


def test_practice_has_no_coaching(harness: Harness) -> None:
    harness.start()

    harness.app.reveal_steps()

    assert harness.screen.hint is None
    assert harness.screen.steps is None
    assert not harness.screen.reveal_enabled


def test_drill_shows_rule_then_mixed_round(harness: Harness) -> None:
    harness.app.start_drill("mul-11")

    assert harness.screen.screen is Screen.GAME
    assert (harness.screen.status_label, harness.screen.time) == ("Problem", "1 / 20")
    assert harness.screen.hint is not None
    assert harness.screen.hint.startswith("×11: digit sum in the middle")
    assert "11" in harness.screen.problem

    for _ in range(10):
        harness.app.answer(harness.current_answer())

    assert harness.screen.time == "11 / 20"
    assert harness.screen.hint is not None
    assert harness.screen.hint.startswith("Mixed round")


def test_drill_reveal_shows_steps_until_the_next_problem(harness: Harness) -> None:
    harness.app.start_drill("mul-11")

    harness.app.reveal_steps()

    assert harness.screen.reveal_enabled
    assert harness.screen.steps is not None
    assert harness.screen.steps.trick_id == "mul-11"

    harness.app.answer(harness.current_answer())

    assert harness.screen.steps is None


def test_finished_drill_reports_and_is_saved(harness: Harness) -> None:
    harness.app.start_drill("div-11")
    for _ in range(20):
        harness.clock.advance(2)
        harness.app.answer(harness.current_answer())

    assert harness.screen.screen is Screen.RESULTS
    report = harness.screen.drill_report
    assert report is not None
    assert report.trick_name == "÷11 from the outer digits"
    assert report.focused_seconds == 2
    assert [r.mode for r in StoredHistory(harness.store).all()] == [
        "Drill: ÷11 from the outer digits"
    ]


def test_play_again_after_a_drill_repeats_the_drill(harness: Harness) -> None:
    harness.app.start_drill("mul-5")
    for _ in range(20):
        harness.app.answer(harness.current_answer())

    harness.app.play_again()

    assert harness.screen.time == "1 / 20"
    assert harness.screen.hint is not None
    assert harness.screen.hint.startswith("×5")


def test_unknown_trick_is_ignored(harness: Harness) -> None:
    harness.app.open_home()

    harness.app.start_drill("no-such-trick")

    assert harness.screen.screen is Screen.HOME


def _slow_multiplication_sessions(history: StoredHistory) -> None:
    """Two practice sessions where ×9 problems are much slower than everything else."""
    fast = [attempt(problem(2, Operation.ADD, 3), seconds=1) for _ in range(6)]
    slow = [attempt(problem(9, Operation.MULTIPLY, 74), seconds=6) for _ in range(3)]
    for _ in range(2):
        history.add(record(attempt(seconds=20), *fast, *slow, mode="Zetamac 120s"))


def test_home_recommends_the_trick_that_saves_most_time(harness: Harness) -> None:
    _slow_multiplication_sessions(StoredHistory(harness.store))

    harness.app.open_home()

    assert [insight.trick_id for insight in harness.screen.recommended] == ["mul-9"]


def test_progress_shows_the_most_played_mode(harness: Harness) -> None:
    history = StoredHistory(harness.store)
    _slow_multiplication_sessions(history)
    history.add(record(attempt(), mode="Zetamac 30s"))

    harness.app.open_progress()

    report = harness.screen.progress
    assert harness.screen.screen is Screen.PROGRESS
    assert report is not None
    assert report.modes == ("Zetamac 120s", "Zetamac 30s")
    assert report.selected is not None
    assert report.selected.mode == "Zetamac 120s"
    assert report.chart is not None
    assert len(report.chart.points) == 2
    assert report.tricks[0].trick_id == "mul-9"
    assert {kind.label for kind in report.kinds} >= {"1-digit + 1-digit", "1-digit × 2-digit"}


def test_progress_can_switch_mode(harness: Harness) -> None:
    history = StoredHistory(harness.store)
    _slow_multiplication_sessions(history)
    history.add(record(attempt(), mode="Zetamac 30s"))

    harness.app.open_progress("Zetamac 30s")

    assert harness.screen.progress is not None
    assert harness.screen.progress.selected is not None
    assert harness.screen.progress.selected.mode == "Zetamac 30s"


def test_progress_without_history(harness: Harness) -> None:
    harness.app.open_progress()

    assert harness.screen.progress == ProgressReport((), None, None, (), ())


def _correct_choice(harness: Harness) -> int:
    """Index of the right option, found by trying each on a copy of the problem."""
    problem = parse_problem_prompt(harness.screen.problem)
    assert harness.screen.choices is not None
    for index, label in enumerate(harness.screen.choices):
        if problem(label):
            return index
    raise AssertionError("no option is correct")


def parse_problem_prompt(prompt: str) -> Callable[[str], bool]:
    """A checker for options of ``a op b = c`` with one part replaced by ``?``."""
    left, symbol, right, _, result = prompt.split(" ")
    functions = {"+": add, "−": sub, "×": mul, "÷": truediv}

    def holds(option: str) -> bool:
        a, b, c = (Fraction(option if part == "?" else part) for part in (left, right, result))
        return bool(functions[symbol](a, b) == c)

    return holds


def test_optiver_uses_multiple_choice_and_scores_plus_minus_one(harness: Harness) -> None:
    harness.app.start_optiver()

    assert harness.screen.choices is not None
    assert len(harness.screen.choices) == 4
    assert harness.screen.status_label == "Time"
    assert harness.screen.time == "8:00 · 1 / 80"

    right = _correct_choice(harness)
    harness.app.choose(right)
    wrong = next(i for i in range(4) if i != _correct_choice(harness))
    harness.app.choose(wrong)
    harness.app.choose(_correct_choice(harness))

    assert harness.screen.score == 1
    assert harness.screen.time == "8:00 · 4 / 80"


def test_optiver_ends_after_80_questions_and_reviews_wrong_answers_first(
    harness: Harness,
) -> None:
    harness.app.start_optiver()
    for question in range(80):
        correct = _correct_choice(harness)
        harness.app.choose(correct if question else (correct + 1) % 4)

    assert harness.screen.screen is Screen.RESULTS
    assert harness.screen.summary is not None
    assert harness.screen.summary.score == 78
    assert harness.screen.review[0].wrong_answer is not None
    assert all(item.wrong_answer is None for item in harness.screen.review[1:])
    assert StoredHistory(harness.store).all()[0].mode == "Optiver 80 in 8"


def test_optiver_ends_when_time_runs_out(harness: Harness) -> None:
    harness.app.start_optiver()
    harness.clock.advance(8 * 60)

    harness.app.tick()

    assert harness.screen.screen is Screen.RESULTS


def test_invalid_choice_is_ignored(harness: Harness) -> None:
    harness.app.start_optiver()
    problem = harness.screen.problem

    harness.app.choose(7)

    assert harness.screen.problem == problem


def test_play_again_after_optiver_repeats_optiver(harness: Harness) -> None:
    harness.app.start_optiver()
    harness.clock.advance(8 * 60)
    harness.app.tick()

    harness.app.play_again()

    assert harness.screen.choices is not None


def test_practice_has_no_choices(harness: Harness) -> None:
    harness.start()

    assert harness.screen.choices is None


def test_export_then_import_into_another_browser(harness: Harness) -> None:
    StoredHistory(harness.store).add(record(attempt(), mode="Zetamac 120s"))
    harness.app.export_data()
    assert harness.screen.download is not None
    filename, content = harness.screen.download
    other = Harness()

    other.app.open_progress()
    other.app.import_data(content)

    assert filename == "armath-backup-2026-09-29.json"
    assert other.screen.backup_message == ("Restored 1 session.", False)
    assert other.screen.progress is not None
    assert other.screen.progress.modes == ("Zetamac 120s",)


def test_importing_again_reports_duplicates(harness: Harness) -> None:
    StoredHistory(harness.store).add(record(attempt()))
    harness.app.export_data()
    assert harness.screen.download is not None

    harness.app.import_data(harness.screen.download[1])

    assert harness.screen.backup_message == ("Restored 0 sessions; 1 was already here.", False)


def test_importing_a_wrong_file_shows_an_error(harness: Harness) -> None:
    harness.app.import_data("hello")

    assert harness.screen.backup_message == ("This file is not valid JSON.", True)


def test_facts_screen_lists_every_deck_as_new(harness: Harness) -> None:
    harness.app.open_facts()

    assert harness.screen.screen is Screen.FACTS
    assert [deck.deck_id for deck in harness.screen.decks] == [
        "tables-12",
        "tables-19",
        "squares",
        "fractions",
    ]
    assert all(deck.new == deck.total for deck in harness.screen.decks)


def test_facts_session_trains_a_deck_and_reports_progress(harness: Harness) -> None:
    harness.app.start_facts("tables-12")
    assert harness.screen.time == "1 / 30"

    for _ in range(30):
        harness.clock.advance(1)
        harness.app.answer(harness.current_answer())

    assert harness.screen.screen is Screen.RESULTS
    assert harness.screen.facts_report == FactsReport("Times tables to 12", 66, 0, 0, 30)
    assert StoredHistory(harness.store).all()[0].kind is SessionKind.FACTS

    harness.app.open_facts()
    tables = harness.screen.decks[0]
    assert (tables.new, tables.learning) == (36, 30)


def test_facts_sessions_stay_out_of_practice_statistics(harness: Harness) -> None:
    harness.app.start_facts("squares")
    for _ in range(15):
        harness.app.answer(harness.current_answer())

    harness.app.open_progress()

    assert harness.screen.progress is not None
    assert harness.screen.progress.modes == ()


def test_play_again_after_facts_repeats_the_deck(harness: Harness) -> None:
    harness.app.start_facts("squares")
    for _ in range(15):
        harness.app.answer(harness.current_answer())

    harness.app.play_again()

    assert harness.screen.screen is Screen.GAME
    assert harness.screen.time == "1 / 15"


def test_unknown_deck_is_ignored(harness: Harness) -> None:
    harness.app.open_facts()

    harness.app.start_facts("no-such-deck")

    assert harness.screen.screen is Screen.FACTS


def test_library_lists_every_trick(harness: Harness) -> None:
    harness.app.open_library()

    assert harness.screen.screen is Screen.LIBRARY
    assert len(harness.screen.library) == len(default_registry().all())


@pytest.mark.parametrize(
    ("seconds", "text"),
    [(120, "2:00"), (59.2, "1:00"), (0.3, "0:01"), (0, "0:00"), (-1, "0:00")],
)
def test_format_clock(seconds: float, text: str) -> None:
    assert format_clock(timedelta(seconds=seconds)) == text
