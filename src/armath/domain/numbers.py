"""Exact numbers and the ways they are written in problems."""

from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from typing import Self


class NumberStyle(StrEnum):
    """How a number is written: ``37``, ``138.6`` or ``3/8``."""

    INTEGER = "integer"
    DECIMAL = "decimal"
    FRACTION = "fraction"


def decimal_places(value: Fraction) -> int | None:
    """Digits needed after the decimal point to write ``value`` exactly.

    Returns ``None`` when the decimal expansion never terminates (e.g. 1/3).
    """
    denominator = value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    return max(twos, fives) if denominator == 1 else None


def can_write(value: Fraction, style: NumberStyle) -> bool:
    """Whether ``value`` can be written exactly in ``style``."""
    match style:
        case NumberStyle.INTEGER:
            return value.denominator == 1
        case NumberStyle.DECIMAL:
            return decimal_places(value) is not None
        case NumberStyle.FRACTION:
            return True


def format_number(value: Fraction, style: NumberStyle) -> str:
    """Write ``value`` exactly in ``style``; raises ``ValueError`` if impossible."""
    if not can_write(value, style):
        raise ValueError(f"{value} cannot be written exactly as {style}")
    if style is NumberStyle.DECIMAL:
        return _format_decimal(value)
    return str(value)


def _format_decimal(value: Fraction) -> str:
    places = decimal_places(value) or 0
    if places == 0:
        return str(value.numerator)
    scaled = abs(value.numerator) * 10**places // value.denominator
    digits = str(scaled).rjust(places + 1, "0")
    sign = "-" if value < 0 else ""
    return f"{sign}{digits[:-places]}.{digits[-places:]}"


def infer_style(value: Fraction, *operand_styles: NumberStyle) -> NumberStyle:
    """Pick a natural style for a computed value given the styles of its operands."""
    if value.denominator == 1:
        return NumberStyle.INTEGER
    if NumberStyle.FRACTION in operand_styles or decimal_places(value) is None:
        return NumberStyle.FRACTION
    return NumberStyle.DECIMAL


@dataclass(frozen=True)
class Operand:
    """An exact number together with the way it is shown to the user."""

    value: Fraction
    style: NumberStyle

    def __post_init__(self) -> None:
        if not can_write(self.value, self.style):
            raise ValueError(f"{self.value} cannot be written exactly as {self.style}")

    @classmethod
    def integer(cls, value: int) -> Self:
        return cls(Fraction(value), NumberStyle.INTEGER)

    @classmethod
    def decimal(cls, value: str | int | Fraction) -> Self:
        return cls(Fraction(value), NumberStyle.DECIMAL)

    @classmethod
    def fraction(cls, numerator: int, denominator: int) -> Self:
        return cls(Fraction(numerator, denominator), NumberStyle.FRACTION)

    def __str__(self) -> str:
        return format_number(self.value, self.style)
