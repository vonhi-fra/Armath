from datetime import UTC, datetime, timedelta
from random import Random

import pytest

from armath import presets
from armath.cli import explain, list_tricks, main, run_session
from armath.modes import ManualClock, Session
from armath.tricks import TrickRegistry, default_registry

START = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)


def test_plays_until_time_runs_out() -> None:
    clock = ManualClock(START)
    session = Session(presets.zetamac(duration=timedelta(seconds=5)), clock, Random(0))
    output: list[str] = []
    answers = iter(["wrong", "correct", "correct", "correct"])

    def read(prompt: str) -> str:
        output.append(prompt)
        clock.advance(2)
        return str(session.current.answer) if next(answers) == "correct" else "nope"

    run_session(session, read, output.append)

    assert "  ✗ try again" in output
    assert output[-2:] == ["Time's up!", "Score: 1"]


def test_explain_shows_best_trick_and_mentions_others() -> None:
    output: list[str] = []

    code = explain("858 / 11", default_registry(), output.append)

    assert code == 0
    assert output[0] == "858 ÷ 11 = ?"
    assert output[2].startswith("÷11 from the outer digits:")
    assert "  3. Put them together:  7 | 8 → 78" in output
    assert "  Answer: 78" in output
    assert output[-1] == "Also works: Missing factor  (use --all)"


def test_explain_every_trick() -> None:
    output: list[str] = []

    explain("11 x 68", default_registry(), output.append, every_trick=True)

    # ×11, round and compensate, vertically and crosswise, split and add
    assert sum(line == "  Answer: 748" for line in output) == 4


def test_explain_reports_bad_input() -> None:
    output: list[str] = []

    assert explain("hello", default_registry(), output.append) == 2
    assert output[0].startswith("not a problem")


def test_explain_reports_problems_without_tricks() -> None:
    output: list[str] = []

    assert explain("7 / 2", TrickRegistry([]), output.append) == 1
    assert output[-1].endswith("No trick covers this problem yet.")


def test_list_tricks_groups_by_operation() -> None:
    output: list[str] = []

    list_tricks(default_registry(), output.append)

    assert output[0] == "Addition"
    assert "Division" in output
    assert any("(general method)" in line for line in output)


def test_main_explain(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["explain", "67 x 11"]) == 0
    assert "6+1 | 3 | 7 → 737" in capsys.readouterr().out
