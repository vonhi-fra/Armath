from datetime import UTC, datetime, timedelta
from random import Random

import pytest

from armath import presets
from armath.domain import Operation
from armath.generators import IntRange, RangeGenerator, ZetamacSettings
from armath.modes import (
    CorrectCount,
    CorrectMinusWrong,
    FirstResponse,
    ManualClock,
    Session,
    SessionOverError,
    SessionPlan,
    UntilCorrect,
)

START = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)
ADDITION = RangeGenerator(Operation.ADD, IntRange(2, 9), IntRange(2, 9))


def _answer(session: Session) -> str:
    return str(session.current.answer)


def _wrong(session: Session) -> str:
    return str(session.current.answer.value + 1)


def _zetamac_session(clock: ManualClock) -> Session:
    return Session(presets.zetamac(duration=timedelta(seconds=10)), clock, Random(0))


def test_correct_answer_is_recorded_with_its_time() -> None:
    clock = ManualClock(START)
    session = _zetamac_session(clock)
    first = session.current

    clock.advance(2.5)
    attempt = session.answer(_answer(session))

    assert attempt is not None
    assert attempt.problem == first
    assert attempt.elapsed_seconds == 2.5
    assert attempt.answered_at == START + timedelta(seconds=2.5)
    assert session.score == 1


def test_time_is_measured_from_when_each_problem_was_shown() -> None:
    clock = ManualClock(START)
    session = _zetamac_session(clock)

    clock.advance(1)
    session.answer(_answer(session))
    clock.advance(3)
    second = session.answer(_answer(session))

    assert second is not None
    assert second.elapsed_seconds == 3


def test_records_when_typing_started() -> None:
    clock = ManualClock(START)
    two_digit_sums = RangeGenerator(Operation.ADD, IntRange(10, 20), IntRange(10, 20))
    plan = SessionPlan(two_digit_sums, CorrectCount(), UntilCorrect(), question_limit=5)
    session = Session(plan, clock, Random(0))
    answer = _answer(session)

    clock.advance(1.5)
    session.answer(answer[0])
    clock.advance(0.5)
    attempt = session.answer(answer)

    assert attempt is not None
    assert attempt.first_input_seconds == 1.5
    assert attempt.elapsed_seconds == 2.0


def test_counts_each_deletion_run_as_one_correction() -> None:
    session = _zetamac_session(ManualClock(START))
    answer = _answer(session)

    # "-" is never a complete answer, so none of these is accepted early.
    for text in ["-", "--", "-", "", "-", "", answer]:  # two separate corrections
        attempt = session.answer(text)

    assert attempt is not None
    assert attempt.corrections == 2
    assert not attempt.is_clean


def test_typing_details_reset_for_each_problem() -> None:
    clock = ManualClock(START)
    session = _zetamac_session(clock)
    session.answer("-")
    session.answer("")
    session.answer(_answer(session))

    clock.advance(1)
    attempt = session.answer(_answer(session))

    assert attempt is not None
    assert attempt.corrections == 0
    assert attempt.first_input_seconds == 1


def test_wrong_or_partial_input_does_not_advance_until_correct() -> None:
    session = _zetamac_session(ManualClock(START))
    problem = session.current

    assert session.answer(_wrong(session)) is None
    assert session.answer("-") is None
    assert session.current == problem
    assert session.attempts == ()


def test_first_response_records_wrong_answers() -> None:
    plan = SessionPlan(ADDITION, CorrectMinusWrong(), FirstResponse(), question_limit=3)
    session = Session(plan, ManualClock(START), Random(0))

    session.answer(_wrong(session))
    session.answer(_answer(session))
    session.answer(_wrong(session))

    assert [attempt.is_correct for attempt in session.attempts] == [False, True, False]
    assert session.score == -1
    assert session.is_over


def test_session_ends_when_time_runs_out() -> None:
    clock = ManualClock(START)
    session = _zetamac_session(clock)

    clock.advance(9.9)
    assert not session.is_over
    assert session.remaining_time == timedelta(seconds=0.1)

    clock.advance(0.2)
    assert session.is_over
    assert session.remaining_time == timedelta(0)
    with pytest.raises(SessionOverError):
        session.answer(_answer(session))


def test_answering_after_question_limit_raises() -> None:
    plan = SessionPlan(ADDITION, CorrectCount(), UntilCorrect(), question_limit=1)
    session = Session(plan, ManualClock(START), Random(0))

    session.answer(_answer(session))

    assert session.remaining_time is None
    with pytest.raises(SessionOverError):
        session.answer("junk")


@pytest.mark.parametrize(
    ("time_limit", "question_limit", "message"),
    [
        (None, None, "needs a time limit"),
        (timedelta(0), None, "time limit must be positive"),
        (None, 0, "question limit must be positive"),
    ],
)
def test_plan_validation(
    time_limit: timedelta | None, question_limit: int | None, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        SessionPlan(ADDITION, CorrectCount(), UntilCorrect(), time_limit, question_limit)


def test_record_captures_the_session() -> None:
    clock = ManualClock(START)
    session = _zetamac_session(clock)
    clock.advance(1)
    session.answer(_answer(session))

    record = session.record()

    assert record.mode == "Zetamac 10s"
    assert record.started_at == START
    assert record.score == 1
    assert record.attempts == session.attempts


def test_preset_name_marks_custom_ranges() -> None:
    custom = ZetamacSettings(addition_left=IntRange(10, 99))

    assert presets.zetamac().name == "Zetamac 120s"
    assert presets.zetamac(custom, timedelta(seconds=60)).name == "Zetamac 60s custom"


def test_manual_clock_rejects_going_backwards() -> None:
    with pytest.raises(ValueError, match="backwards"):
        ManualClock(START).advance(-1)


def test_manual_clock_moves_wall_and_monotonic_time_together() -> None:
    clock = ManualClock(START)

    clock.advance(2.5)

    assert clock.now() == START + timedelta(seconds=2.5)
    assert clock.monotonic() == 2.5
