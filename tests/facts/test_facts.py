from dataclasses import replace
from datetime import timedelta
from fractions import Fraction
from random import Random

import pytest
from factories import START, record

from armath.domain import Attempt, Operation, SessionKind, SessionRecord
from armath.facts import (
    DECKS,
    FactMemory,
    FactQueue,
    FactsTraining,
    Grade,
    choose_facts,
    deck_by_id,
    deck_progress,
    fact_key,
    grade,
)
from armath.facts.deck import Fact, fraction_decimals, squares, times_tables
from armath.facts.memory import INTERVALS
from armath.modes import ManualClock, Session

TABLES = times_tables(12)


def _answer(fact: Fact, *, seconds: float = 1.0, corrections: int = 0, day: float = 0) -> Attempt:
    problem = fact.problem()
    return Attempt(
        problem,
        problem.answer.value,
        seconds,
        START + timedelta(days=day),
        corrections=corrections,
    )


def _facts_session(*attempts: Attempt) -> SessionRecord:
    return replace(record(*attempts), kind=SessionKind.FACTS)


# Decks


def test_decks_have_the_expected_sizes() -> None:
    assert len(times_tables(12).facts) == 66  # 2..12, a ≤ b
    assert len(times_tables(19).facts) == 171  # 18 numbers: 18 × 19 / 2
    assert len(squares().facts) == 15


def test_every_fraction_fact_has_an_exact_decimal_answer() -> None:
    for fact in fraction_decimals().facts:
        answer = fact.problem().answer
        assert str(answer).startswith("0.")
        assert Fraction(str(answer)) == Fraction(fact.left, fact.right)


def test_tables_are_introduced_easiest_first() -> None:
    first = [(f.left, f.right) for f in TABLES.facts[:4]]

    assert first == [(2, 2), (2, 3), (3, 3), (2, 4)]


def test_multiplication_facts_share_a_key_in_either_order() -> None:
    fact = Fact(7, Operation.MULTIPLY, 8)
    rng = Random(0)
    keys = {fact_key(fact.problem(rng)) for _ in range(20)}

    assert keys == {"7 × 8"}


def test_deck_lookup() -> None:
    assert deck_by_id("squares").name == "Squares 11 to 25"
    with pytest.raises(KeyError):
        deck_by_id("nope")
    assert len({deck.id for deck in DECKS}) == len(DECKS)


# Grading and memory


@pytest.mark.parametrize(
    ("seconds", "corrections", "expected"),
    [(1.2, 0, Grade.GOOD), (2.0, 0, Grade.SLOW), (4.0, 0, Grade.MISSED), (1.0, 1, Grade.MISSED)],
)
def test_grade(seconds: float, corrections: int, expected: Grade) -> None:
    # 7 × 8 = 56: target 1.0 + 2 × 0.35 = 1.7s
    fact = Fact(7, Operation.MULTIPLY, 8)

    assert grade(_answer(fact, seconds=seconds, corrections=corrections)) is expected


def test_fast_answers_climb_the_boxes_and_misses_start_over() -> None:
    fact = Fact(7, Operation.MULTIPLY, 8)
    memory = FactMemory()

    for day in range(4):
        memory.learn(_answer(fact, day=day))
    climbed = memory.state(fact.key)
    memory.learn(_answer(fact, corrections=1, day=10))
    missed = memory.state(fact.key)

    assert climbed is not None
    assert climbed.box == 4
    assert climbed.mastered
    assert climbed.due == START + timedelta(days=3) + INTERVALS[4]
    assert missed is not None
    assert (missed.box, missed.reviews, missed.mastered) == (0, 5, False)


def test_memory_is_replayed_from_fact_sessions_only() -> None:
    fact = Fact(7, Operation.MULTIPLY, 8)
    practice = record(_answer(fact))  # a practice session also asked 7 × 8

    memory = FactMemory.replay([practice, _facts_session(_answer(fact))])

    state = memory.state(fact.key)
    assert state is not None
    assert state.reviews == 1


# Choosing facts


def test_fresh_deck_starts_with_the_easiest_facts() -> None:
    picked = choose_facts(TABLES, FactMemory(), START, Random(0), size=10, new_limit=4)

    assert sorted((f.left, f.right) for f in picked) == sorted(
        (f.left, f.right) for f in TABLES.facts[:10]
    )


def test_due_facts_come_first_and_new_ones_are_limited() -> None:
    memory = FactMemory()
    due = TABLES.facts[:5]
    for fact in due:
        memory.learn(_answer(fact, seconds=5))  # missed: due again right away
    for fact in TABLES.facts[5:20]:
        memory.learn(_answer(fact))  # known: due tomorrow

    picked = choose_facts(
        TABLES, memory, START + timedelta(hours=1), Random(0), size=10, new_limit=3
    )

    assert set(due) <= set(picked)
    assert len([f for f in picked if memory.state(f.key) is None]) == 3
    assert len(picked) == 10


# The session queue


def test_missed_fact_comes_back_after_a_gap_and_the_length_stays_fixed() -> None:
    facts = list(TABLES.facts[:6])
    queue = FactQueue(facts, TABLES)
    rng = Random(0)

    first = queue.generate(rng)
    queue.attempted(Attempt(first, first.answer.value, 9.0, START))
    rest = [fact_key(queue.generate(rng)) for _ in range(5)]

    assert rest[3] == fact_key(first)
    assert fact_key(facts[-1].problem()) not in rest  # pushed off the end


def test_a_fact_is_asked_at_most_three_times_per_session() -> None:
    hard = TABLES.facts[0]
    queue = FactQueue(list(TABLES.facts[:12]), TABLES)
    rng = Random(0)
    asked = 0
    for _ in range(12):
        problem = queue.generate(rng)
        if fact_key(problem) == hard.key:
            asked += 1
            queue.attempted(Attempt(problem, problem.answer.value, 9.0, START))  # always missed

    assert asked == 3


def test_training_session_and_report() -> None:
    clock = ManualClock(START)
    training = FactsTraining(TABLES, [], START, Random(0))
    session = Session(training.plan(), clock, Random(0))

    while not session.is_over:
        clock.advance(1)
        session.answer(str(session.current.answer))

    finished = session.record()
    report = training.report([finished])
    progress = deck_progress(TABLES, FactMemory.replay([finished]), START)

    assert finished.kind is SessionKind.FACTS
    assert finished.mode == "Facts: Times tables to 12"
    assert len(finished.attempts) == 30
    assert report.new_seen == 30
    assert report.mastered_before == report.mastered_after == 0
    assert (progress.new, progress.learning, progress.due) == (36, 30, 0)
    assert len(progress.grid) == 11 * 11
    assert {cell.box for cell in progress.grid} == {None, 1}
