from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st

from armath.domain import NumberStyle, Operand, format_number, parse_answer
from armath.domain.numbers import decimal_places, infer_style


@pytest.mark.parametrize(
    ("value", "places"),
    [
        (Fraction(7), 0),
        (Fraction(1, 2), 1),
        (Fraction(1, 8), 3),
        (Fraction(693, 5), 1),
        (Fraction(1, 3), None),
        (Fraction(1, 7), None),
    ],
)
def test_decimal_places(value: Fraction, places: int | None) -> None:
    assert decimal_places(value) == places


@pytest.mark.parametrize(
    ("value", "style", "text"),
    [
        (Fraction(37), NumberStyle.INTEGER, "37"),
        (Fraction(-4), NumberStyle.INTEGER, "-4"),
        (Fraction("138.6"), NumberStyle.DECIMAL, "138.6"),
        (Fraction(1, 8), NumberStyle.DECIMAL, "0.125"),
        (Fraction(-1, 20), NumberStyle.DECIMAL, "-0.05"),
        (Fraction(5), NumberStyle.DECIMAL, "5"),
        (Fraction(3, 8), NumberStyle.FRACTION, "3/8"),
        (Fraction(-2, 3), NumberStyle.FRACTION, "-2/3"),
        (Fraction(4), NumberStyle.FRACTION, "4"),
    ],
)
def test_format_number(value: Fraction, style: NumberStyle, text: str) -> None:
    assert format_number(value, style) == text


@pytest.mark.parametrize(
    ("value", "style"),
    [(Fraction(1, 2), NumberStyle.INTEGER), (Fraction(1, 3), NumberStyle.DECIMAL)],
)
def test_format_number_rejects_inexact_styles(value: Fraction, style: NumberStyle) -> None:
    with pytest.raises(ValueError, match="cannot be written"):
        format_number(value, style)


@pytest.mark.parametrize(
    ("value", "operand_styles", "expected"),
    [
        (Fraction(12), (NumberStyle.DECIMAL,), NumberStyle.INTEGER),
        (Fraction(7, 2), (NumberStyle.INTEGER, NumberStyle.INTEGER), NumberStyle.DECIMAL),
        (Fraction(1, 3), (NumberStyle.INTEGER,), NumberStyle.FRACTION),
        (Fraction(5, 8), (NumberStyle.FRACTION, NumberStyle.INTEGER), NumberStyle.FRACTION),
    ],
)
def test_infer_style(
    value: Fraction, operand_styles: tuple[NumberStyle, ...], expected: NumberStyle
) -> None:
    assert infer_style(value, *operand_styles) is expected


def test_operand_factories() -> None:
    assert str(Operand.integer(12)) == "12"
    assert str(Operand.decimal("0.25")) == "0.25"
    assert str(Operand.fraction(6, 8)) == "3/4"


def test_operand_rejects_value_its_style_cannot_show() -> None:
    with pytest.raises(ValueError, match="cannot be written"):
        Operand(Fraction(1, 2), NumberStyle.INTEGER)


terminating_decimals = st.builds(
    lambda numerator, places: Fraction(numerator, 10**places),
    st.integers(-(10**9), 10**9),
    st.integers(0, 6),
)


@given(terminating_decimals)
def test_decimal_text_parses_back_to_the_same_value(value: Fraction) -> None:
    assert parse_answer(format_number(value, NumberStyle.DECIMAL)) == value


@given(st.fractions())
def test_fraction_text_parses_back_to_the_same_value(value: Fraction) -> None:
    assert parse_answer(format_number(value, NumberStyle.FRACTION)) == value
