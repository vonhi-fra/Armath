from datetime import UTC, datetime, timedelta
from random import Random

from armath import presets
from armath.cli import run_session
from armath.modes import ManualClock, Session

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
