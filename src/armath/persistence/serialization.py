"""Converting domain objects to and from JSON-compatible dicts.

Numbers are stored as exact fraction strings (``"693/5"``) so nothing is lost to floats.
Every ``*_from_dict`` raises ``KeyError``, ``TypeError`` or ``ValueError`` on malformed data.
"""

from datetime import datetime
from fractions import Fraction
from typing import Any

from armath.domain import (
    Attempt,
    NumberStyle,
    Operand,
    Operation,
    Problem,
    SessionRecord,
    Unknown,
)
from armath.generators import IntRange, ZetamacSettings
from armath.settings import PracticeSettings

type JsonDict = dict[str, Any]


def operand_to_dict(operand: Operand) -> JsonDict:
    return {"value": str(operand.value), "style": operand.style.value}


def operand_from_dict(data: JsonDict) -> Operand:
    return Operand(Fraction(data["value"]), NumberStyle(data["style"]))


def problem_to_dict(problem: Problem) -> JsonDict:
    return {
        "left": operand_to_dict(problem.left),
        "operation": problem.operation.name,
        "right": operand_to_dict(problem.right),
        "result": operand_to_dict(problem.result),
        "unknown": problem.unknown.value,
    }


def problem_from_dict(data: JsonDict) -> Problem:
    return Problem(
        left=operand_from_dict(data["left"]),
        operation=Operation[data["operation"]],
        right=operand_from_dict(data["right"]),
        result=operand_from_dict(data["result"]),
        unknown=Unknown(data["unknown"]),
    )


def attempt_to_dict(attempt: Attempt) -> JsonDict:
    return {
        "problem": problem_to_dict(attempt.problem),
        "response": str(attempt.response),
        "elapsed_seconds": attempt.elapsed_seconds,
        "answered_at": attempt.answered_at.isoformat(),
    }


def attempt_from_dict(data: JsonDict) -> Attempt:
    return Attempt(
        problem=problem_from_dict(data["problem"]),
        response=Fraction(data["response"]),
        elapsed_seconds=float(data["elapsed_seconds"]),
        answered_at=datetime.fromisoformat(data["answered_at"]),
    )


def record_to_dict(record: SessionRecord) -> JsonDict:
    return {
        "mode": record.mode,
        "started_at": record.started_at.isoformat(),
        "score": record.score,
        "attempts": [attempt_to_dict(attempt) for attempt in record.attempts],
    }


def record_from_dict(data: JsonDict) -> SessionRecord:
    return SessionRecord(
        mode=str(data["mode"]),
        started_at=datetime.fromisoformat(data["started_at"]),
        score=int(data["score"]),
        attempts=tuple(attempt_from_dict(item) for item in data["attempts"]),
    )


def _range_to_list(int_range: IntRange) -> list[int]:
    return [int_range.low, int_range.high]


def _range_from_list(data: list[int]) -> IntRange:
    low, high = data
    return IntRange(int(low), int(high))


def settings_to_dict(settings: PracticeSettings) -> JsonDict:
    zetamac = settings.zetamac
    return {
        "duration_seconds": settings.duration_seconds,
        "zetamac": {
            "addition_left": _range_to_list(zetamac.addition_left),
            "addition_right": _range_to_list(zetamac.addition_right),
            "multiplication_left": _range_to_list(zetamac.multiplication_left),
            "multiplication_right": _range_to_list(zetamac.multiplication_right),
            "operations": [op.name for op in Operation if op in zetamac.operations],
        },
    }


def settings_from_dict(data: JsonDict) -> PracticeSettings:
    zetamac = data["zetamac"]
    return PracticeSettings(
        zetamac=ZetamacSettings(
            addition_left=_range_from_list(zetamac["addition_left"]),
            addition_right=_range_from_list(zetamac["addition_right"]),
            multiplication_left=_range_from_list(zetamac["multiplication_left"]),
            multiplication_right=_range_from_list(zetamac["multiplication_right"]),
            operations=frozenset(Operation[name] for name in zetamac["operations"]),
        ),
        duration_seconds=int(data["duration_seconds"]),
    )
