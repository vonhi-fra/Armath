from fractions import Fraction

import pytest

from armath.domain import parse_answer


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("42", Fraction(42)),
        ("  42 ", Fraction(42)),
        ("-3", Fraction(-3)),
        ("−3", Fraction(-3)),
        ("0.125", Fraction(1, 8)),
        (".5", Fraction(1, 2)),
        ("5.", Fraction(5)),
        ("0,5", Fraction(1, 2)),
        ("3/8", Fraction(3, 8)),
        ("6 / 8", Fraction(3, 4)),
    ],
)
def test_parses_valid_answers(text: str, expected: Fraction) -> None:
    assert parse_answer(text) == expected


@pytest.mark.parametrize(
    "text", ["", "-", ".", "abc", "1e3", "1_000", "1/0", "1/", "/2", "1.5/2", "+-1", "--1"]
)
def test_rejects_incomplete_or_invalid_answers(text: str) -> None:
    assert parse_answer(text) is None
