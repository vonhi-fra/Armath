from dataclasses import replace
from datetime import timedelta

from factories import START, attempt, record

from armath.analytics import mode_progress
from armath.domain import SessionKind


def test_progress_per_practice_mode_most_played_first() -> None:
    history = [
        replace(record(attempt(), mode="A", score=10), started_at=START),
        replace(record(attempt(), mode="B", score=40), started_at=START + timedelta(days=1)),
        replace(record(attempt(), mode="A", score=30), started_at=START + timedelta(days=2)),
        replace(record(attempt(), mode="Drill", score=99), kind=SessionKind.DRILL),
    ]

    progress = mode_progress(history)

    assert [item.mode for item in progress] == ["A", "B"]
    assert [point.score for point in progress[0].points] == [10, 30]
    assert (progress[0].sessions, progress[0].best, progress[0].latest) == (2, 30, 30)


def test_ties_go_to_the_most_recently_played_mode() -> None:
    history = [
        replace(record(attempt(), mode="old"), started_at=START),
        replace(record(attempt(), mode="new"), started_at=START + timedelta(days=1)),
    ]

    assert [item.mode for item in mode_progress(history)] == ["new", "old"]
