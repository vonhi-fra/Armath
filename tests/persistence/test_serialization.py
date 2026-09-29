import json

import pytest
from factories import attempt, problem, record

from armath.domain import Operand, Operation, Problem, Unknown
from armath.generators import IntRange, ZetamacSettings
from armath.persistence.serialization import (
    problem_from_dict,
    problem_to_dict,
    record_from_dict,
    record_to_dict,
    settings_from_dict,
    settings_to_dict,
)
from armath.settings import PracticeSettings


def _json_round_trip[T](data: T) -> T:
    loaded: T = json.loads(json.dumps(data))
    return loaded


def test_problem_round_trip_keeps_exact_values_and_styles() -> None:
    original = Problem.create(
        Operand.integer(66), Operation.MULTIPLY, Operand.decimal("2.1"), unknown=Unknown.RIGHT
    )

    restored = problem_from_dict(_json_round_trip(problem_to_dict(original)))

    assert restored == original
    assert restored.prompt == "66 × ? = 138.6"


def test_record_round_trip() -> None:
    original = record(attempt(problem(12, Operation.ADD, 30)), attempt(correct=False, seconds=4.5))

    assert record_from_dict(_json_round_trip(record_to_dict(original))) == original


def test_record_round_trip_keeps_typing_details() -> None:
    original = record(attempt(corrections=2))

    restored = record_from_dict(_json_round_trip(record_to_dict(original)))

    assert restored.attempts[0].corrections == 2
    assert restored.attempts[0].first_input_seconds == 1.0


def test_records_saved_before_typing_details_still_load() -> None:
    data = record_to_dict(record(attempt()))
    for item in data["attempts"]:
        del item["first_input_seconds"], item["corrections"]

    restored = record_from_dict(_json_round_trip(data))

    assert restored.attempts[0].first_input_seconds is None
    assert restored.attempts[0].corrections == 0


def test_settings_round_trip() -> None:
    original = PracticeSettings(
        zetamac=ZetamacSettings(
            addition_left=IntRange(10, 99),
            operations=frozenset({Operation.ADD, Operation.MULTIPLY}),
        ),
        duration_seconds=60,
    )

    assert settings_from_dict(_json_round_trip(settings_to_dict(original))) == original


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"left": {"value": "1", "style": "integer"}},
        {**problem_to_dict(problem()), "operation": "POWER"},
        {**problem_to_dict(problem()), "result": {"value": "41", "style": "integer"}},
    ],
)
def test_malformed_problem_raises(data: dict[str, object]) -> None:
    with pytest.raises((KeyError, TypeError, ValueError)):
        problem_from_dict(data)
