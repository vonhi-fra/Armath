from dataclasses import replace

import pytest

from armath.domain import Operation
from armath.generators import IntRange, ZetamacSettings
from armath.settings import PracticeSettings
from armath.ui import FormError, RangeFields, SettingsForm

DEFAULT_FORM = SettingsForm.from_settings(PracticeSettings())


def _errors(form: SettingsForm) -> list[str]:
    with pytest.raises(FormError) as caught:
        form.parse()
    return caught.value.messages


def test_default_form_parses_to_default_settings() -> None:
    assert DEFAULT_FORM.parse() == PracticeSettings()


def test_custom_values_are_parsed() -> None:
    form = replace(
        DEFAULT_FORM,
        addition_left=RangeFields(" 10 ", "99"),
        operations=frozenset({Operation.ADD}),
        duration_seconds="60",
    )

    assert form.parse() == PracticeSettings(
        zetamac=ZetamacSettings(
            addition_left=IntRange(10, 99), operations=frozenset({Operation.ADD})
        ),
        duration_seconds=60,
    )


def test_reports_every_problem_at_once() -> None:
    form = replace(
        DEFAULT_FORM,
        addition_left=RangeFields("abc", "10"),
        multiplication_right=RangeFields("50", "5"),
        duration_seconds="0",
        operations=frozenset(),
    )

    assert _errors(form) == [
        "Addition, left (from): 'abc' is not a whole number.",
        "Multiplication, right: 'from' must not be greater than 'to'.",
        "Duration must be at least 1.",
        "Pick at least one operation.",
    ]


def test_division_needs_nonzero_divisors() -> None:
    form = replace(DEFAULT_FORM, multiplication_left=RangeFields("0", "12"))

    assert _errors(form) == ["Division needs a left multiplication range without 0."]


def test_zero_divisors_are_fine_without_division() -> None:
    form = replace(
        DEFAULT_FORM,
        multiplication_left=RangeFields("0", "12"),
        operations=frozenset({Operation.MULTIPLY}),
    )

    assert form.parse().zetamac.multiplication_left == IntRange(0, 12)
