from dataclasses import replace

import pytest
from factories import attempt, problem, record

from armath.analytics import (
    kind_insights,
    recent_practice,
    recommendations,
    trick_insights,
)
from armath.domain import Attempt, Operation, SessionKind, SessionRecord
from armath.tricks import default_registry

REGISTRY = default_registry()
WARM_UP = attempt(seconds=30)


def _add(seconds: float) -> Attempt:
    return attempt(problem(2, Operation.ADD, 3), seconds=seconds)


def _times_nine(seconds: float) -> Attempt:
    return attempt(problem(9, Operation.MULTIPLY, 74), seconds=seconds)


def _session(*attempts: Attempt, kind: SessionKind = SessionKind.PRACTICE) -> SessionRecord:
    return replace(record(WARM_UP, *attempts), kind=kind)


def test_recent_practice_skips_drills_and_warm_ups() -> None:
    practice = _session(_add(1))
    drill = _session(_add(1), kind=SessionKind.DRILL)

    assert recent_practice([practice, drill, practice]) == [[_add(1)], [_add(1)]]


def test_recent_practice_keeps_only_the_latest_sessions() -> None:
    sessions = [_session(_add(seconds)) for seconds in (1, 2, 3)]

    assert recent_practice(sessions, sessions=2) == [[_add(2)], [_add(3)]]


def test_time_lost_is_credited_to_the_best_trick() -> None:
    history = [_session(_add(1), _add(1), _add(1), _times_nine(4), _times_nine(6))]

    insights = trick_insights(history, REGISTRY)

    by_id = {insight.trick_id: insight for insight in insights}
    assert insights[0].trick_id == "mul-9"
    assert by_id["mul-9"].problems == 2
    assert by_id["mul-9"].median_seconds == 5
    assert by_id["mul-9"].share_of_time_lost == 1
    assert by_id["add-left-to-right"].share_of_time_lost == 0


def test_trend_compares_older_and_newer_sessions() -> None:
    older = _session(*[_times_nine(6)] * 3, _add(1))
    newer = _session(*[_times_nine(3)] * 3, _add(1))

    (nine,) = [i for i in trick_insights([older, newer], REGISTRY) if i.trick_id == "mul-9"]

    assert (nine.earlier_seconds, nine.recent_seconds) == (6, 3)


def test_trend_needs_enough_problems() -> None:
    older = _session(_times_nine(6), _add(1))
    newer = _session(_times_nine(3), _add(1))

    (nine,) = [i for i in trick_insights([older, newer], REGISTRY) if i.trick_id == "mul-9"]

    assert nine.earlier_seconds is None


def test_recommendations_need_enough_problems_and_lost_time() -> None:
    # Mostly fast additions, so the typical time is 1s and slow ×9 problems lose time.
    few = trick_insights([_session(*[_add(1)] * 5, _times_nine(6))], REGISTRY)
    enough = trick_insights([_session(*[_add(1)] * 5, *[_times_nine(6)] * 4)], REGISTRY)

    assert recommendations(few) == []
    assert [insight.trick_id for insight in recommendations(enough)] == ["mul-9"]


def test_no_history_means_no_insights() -> None:
    assert trick_insights([], REGISTRY) == []
    assert kind_insights([]) == []


def test_kind_insights_group_problems() -> None:
    history = [_session(_add(1), _add(3), _times_nine(5), attempt(corrections=1))]

    insights = {insight.label: insight for insight in kind_insights(history)}

    assert insights["1-digit + 1-digit"].problems == 2
    assert insights["1-digit + 1-digit"].median_seconds == 2
    assert insights["1-digit × 1-digit"].first_try_rate == 0
    assert next(iter(insights)) == "1-digit + 1-digit"


@pytest.mark.parametrize("sessions", [0, 1])
def test_single_session_trend_is_all_recent(sessions: int) -> None:
    history = [_session(*[_times_nine(4)] * 3) for _ in range(sessions + 1)]

    (nine,) = trick_insights(history, REGISTRY)

    assert nine.recent_seconds == 4
