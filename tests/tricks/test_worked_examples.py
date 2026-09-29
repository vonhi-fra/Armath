"""The exact steps shown for known examples (the ones in docs/research.md §6)."""

import pytest

from armath.domain import Operand, Operation, Problem
from armath.tricks import default_registry

REGISTRY = default_registry()
SYMBOLS = {
    "+": Operation.ADD,
    "-": Operation.SUBTRACT,
    "x": Operation.MULTIPLY,
    "/": Operation.DIVIDE,
}


def _problem(text: str) -> Problem:
    left, symbol, right = text.split()
    return Problem.create(Operand.integer(int(left)), SYMBOLS[symbol], Operand.integer(int(right)))


@pytest.mark.parametrize(
    ("trick_id", "problem", "work"),
    [
        ("add-left-to-right", "67 + 58", ["67 + 50 = 117", "117 + 8 = 125"]),
        ("add-round-up", "47 + 38", ["47 + 40 = 87", "87 − 2 = 85"]),
        ("sub-left-to-right", "145 - 62", ["145 − 60 = 85", "85 − 2 = 83"]),
        ("sub-round-up", "131 - 69", ["131 − 70 = 61", "61 + 1 = 62"]),
        ("sub-count-up", "132 - 87", ["100 − 87 = 13", "132 − 100 = 32", "13 + 32 = 45"]),
        ("sub-count-up", "100 - 37", ["100 − 37 = 63"]),
        ("mul-split", "7 x 68", ["7 × 60 = 420", "7 × 8 = 56", "420 + 56 = 476"]),
        (
            "mul-split",
            "7 x 123",
            ["7 × 100 = 700", "7 × 20 = 140", "7 × 3 = 21", "700 + 140 = 840", "840 + 21 = 861"],
        ),
        ("mul-split", "7 x 8", ["7 × 8 = 56"]),
        ("mul-round-up", "7 x 69", ["7 × 70 = 490", "490 − 7 = 483"]),
        ("mul-round-up", "7 x 68", ["7 × 70 = 490", "7 × 2 = 14", "490 − 14 = 476"]),
        ("mul-5", "5 x 68", ["68 ÷ 2 = 34", "34 × 10 = 340"]),
        ("mul-5", "37 x 5", ["37 × 10 = 370", "370 ÷ 2 = 185"]),
        ("mul-25-50", "8 x 25", ["8 ÷ 4 = 2", "2 × 100 = 200"]),
        ("mul-25-50", "7 x 25", ["7 × 100 = 700", "700 ÷ 4 = 175"]),
        ("mul-25-50", "7 x 50", ["7 × 100 = 700", "700 ÷ 2 = 350"]),
        ("mul-9", "9 x 74", ["74 × 10 = 740", "740 − 74 = 666"]),
        ("mul-9", "7 x 99", ["7 × 100 = 700", "700 − 7 = 693"]),
        ("mul-11", "11 x 35", ["3 + 5 = 8", "3 | 8 | 5 → 385"]),
        ("mul-11", "11 x 67", ["6 + 7 = 13", "6+1 | 3 | 7 → 737"]),
        ("mul-12", "12 x 47", ["47 × 10 = 470", "47 × 2 = 94", "470 + 94 = 564"]),
        ("mul-halve-double", "6 x 45", ["6 ÷ 2 = 3", "45 × 2 = 90", "3 × 90 = 270"]),
        ("mul-double", "8 x 37", ["37 × 2 = 74", "74 × 2 = 148", "148 × 2 = 296"]),
        (
            "div-chunk",
            "648 / 12",
            ["12 × 50 = 600", "648 − 600 = 48", "12 × 4 = 48, so 48 ÷ 12 = 4", "50 + 4 = 54"],
        ),
        ("div-chunk", "96 / 12", ["12 × 8 = 96, so 96 ÷ 12 = 8"]),
        ("div-chunk", "360 / 9", ["9 × 40 = 360", "360 ÷ 9 = 40"]),
        ("div-5", "345 / 5", ["345 × 2 = 690", "690 ÷ 10 = 69"]),
        ("div-halve-both", "432 / 12", ["432 ÷ 12 → 216 ÷ 6", "216 ÷ 6 → 108 ÷ 3", "108 ÷ 3 = 36"]),
        ("div-11", "858 / 11", ["8 − 1 = 7", "858 → 8", "7 | 8 → 78"]),
        ("div-11", "253 / 11", ["253 → 2", "253 → 3", "2 | 3 → 23"]),
        ("div-11", "1045 / 11", ["10 − 1 = 9", "1045 → 5", "9 | 5 → 95"]),
        ("div-9", "423 / 9", ["423 → 42", "9 × 4 ≤ 42 → 4", "10 − 3 = 7", "4 | 7 → 47"]),
        ("div-9", "99 / 9", ["99 → 9", "9 × 1 ≤ 9 → 1", "10 − 9 = 1", "1 | 1 → 11"]),
    ],
)
def test_worked_example(trick_id: str, problem: str, work: list[str]) -> None:
    explanation = REGISTRY.get(trick_id).explain(_problem(problem))

    assert [step.work for step in explanation.steps] == work


@pytest.mark.parametrize(
    ("problem", "best"),
    [
        ("11 x 67", "mul-11"),
        ("9 x 74", "mul-9"),
        ("7 x 68", "mul-round-up"),
        ("7 x 63", "mul-split"),
        ("12 x 7", "mul-split"),
        ("5 x 68", "mul-5"),
        ("858 / 11", "div-11"),
        ("96 / 12", "div-chunk"),
        ("47 + 38", "add-round-up"),
        ("42 + 31", "add-left-to-right"),
        ("131 - 69", "sub-round-up"),
        ("132 - 84", "sub-count-up"),
    ],
)
def test_best_trick(problem: str, best: str) -> None:
    trick = REGISTRY.best(_problem(problem))

    assert trick is not None
    assert trick.id == best


@pytest.mark.parametrize(
    ("trick_id", "problem"),
    [
        ("mul-11", "11 x 7"),  # single digit: times table
        ("mul-11", "11 x 100"),
        ("mul-5", "5 x 7"),
        ("mul-12", "12 x 11"),
        ("div-9", "360 / 9"),  # quotient ends in 0: the digit rule breaks
        ("div-11", "99 / 11"),
        ("div-halve-both", "96 / 12"),  # quotient in the times table
        ("sub-count-up", "95 - 37"),  # doesn't cross a hundred
        ("add-round-up", "43 + 52"),
    ],
)
def test_trick_does_not_apply(trick_id: str, problem: str) -> None:
    assert not REGISTRY.get(trick_id).applies_to(_problem(problem))
