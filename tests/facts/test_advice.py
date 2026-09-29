from dataclasses import replace

import pytest
from factories import attempt, problem, record

from armath.domain import Attempt, Operand, Operation, Problem, SessionKind
from armath.facts import advise, table_fact


@pytest.mark.parametrize(
    ("the_problem", "fact"),
    [
        (problem(8, Operation.MULTIPLY, 7), "7 × 8"),
        (problem(56, Operation.DIVIDE, 7), "7 × 8"),
        (problem(12, Operation.MULTIPLY, 12), "12 × 12"),
        (problem(13, Operation.MULTIPLY, 7), None),  # beyond the 12 times table
        (problem(7, Operation.ADD, 8), None),
        (Problem.create(Operand.decimal("0.5"), Operation.MULTIPLY, Operand.integer(8)), None),
    ],
)
def test_table_fact(the_problem: Problem, fact: str | None) -> None:
    assert table_fact(the_problem) == fact


def _slow(a: int, b: int) -> Attempt:
    return attempt(problem(a, Operation.MULTIPLY, b), seconds=4)


def test_advice_needs_several_slow_facts() -> None:
    few = record(attempt(), _slow(7, 8), _slow(6, 7))
    enough = record(attempt(), _slow(7, 8), _slow(6, 7), _slow(8, 7), _slow(9, 6))

    assert advise([few]) is None
    advice = advise([enough])
    assert advice is not None
    assert advice.count == 3  # 7 × 8 counted once
    assert advice.slow_facts == ("7 × 8", "6 × 7", "6 × 9")


def test_fast_facts_and_fact_sessions_do_not_count() -> None:
    fast = record(
        attempt(), *(attempt(problem(a, Operation.MULTIPLY, 7), seconds=1) for a in (3, 4, 6))
    )
    facts_session = replace(
        record(attempt(), _slow(7, 8), _slow(6, 7), _slow(9, 6)), kind=SessionKind.FACTS
    )

    assert advise([fast, facts_session]) is None
