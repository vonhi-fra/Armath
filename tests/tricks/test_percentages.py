from collections import Counter
from dataclasses import replace
from fractions import Fraction
from random import Random

import pytest

from armath.domain import (
    NumberStyle,
    Operand,
    Operation,
    Problem,
    Unknown,
    parse_answer,
    parse_problem,
)
from armath.generators import optiver_generator
from armath.modes import PlausibleChoices
from armath.tricks import default_registry

REGISTRY = default_registry()
MUL, DIV = Operation.MULTIPLY, Operation.DIVIDE


def _of(percentage: str, base: int) -> Problem:
    return Problem.create(Operand.percent(percentage), MUL, Operand.integer(base))


# Writing and reading percentages


def test_percent_is_a_way_of_writing_a_value() -> None:
    fifteen = Operand.percent(15)

    assert fifteen.value == Fraction(3, 20)
    assert str(fifteen) == "15%"
    assert str(Operand.percent("12.5")) == "12.5%"


def test_percent_of_reads_naturally() -> None:
    problem = _of("15", 240)

    assert problem.prompt == "15% of 240 = ?"
    assert problem.equation == "15% of 240 = 36"
    assert problem.answer == Operand.integer(36)


def test_missing_percentage_is_marked() -> None:
    problem = replace(_of("15", 240), unknown=Unknown.LEFT)

    assert problem.prompt == "?% of 240 = 36"
    assert str(problem.answer) == "15%"


@pytest.mark.parametrize(("text", "value"), [("15%", Fraction(3, 20)), ("12.5%", Fraction(1, 8))])
def test_typed_percentages(text: str, value: Fraction) -> None:
    assert parse_answer(text) == value


def test_explain_command_reads_percentages() -> None:
    assert parse_problem("15% of 240") == _of("15", 240)


# Tricks


@pytest.mark.parametrize(
    ("problem", "best", "work"),
    [
        (_of("15", 240), "pct-tens", ["240 ÷ 10 = 24", "24 ÷ 2 = 12", "24 + 12 = 36"]),
        (_of("35", 60), "pct-tens", ["60 ÷ 10 = 6", "6 × 3 = 18", "6 ÷ 2 = 3", "18 + 3 = 21"]),
        (
            _of("18", 300),
            "pct-tens",
            ["300 ÷ 10 = 30", "300 ÷ 100 = 3", "3 × 8 = 24", "30 + 24 = 54"],
        ),
        (_of("25", 240), "pct-fraction", ["25% = 1/4", "240 ÷ 4 = 60"]),
        (_of("75", 80), "pct-fraction", ["75% = 3/4", "80 ÷ 4 = 20", "20 × 3 = 60"]),
        (_of("12.5", 64), "pct-fraction", ["12.5% = 1/8", "64 ÷ 8 = 8"]),
        (_of("24", 50), "pct-swap", ["24% of 50 = 50% of 24", "24 ÷ 2 = 12"]),
        (
            Problem.create(
                Operand.integer(36), DIV, Operand.integer(240), result_style=NumberStyle.PERCENT
            ),
            "pct-what-percent",
            ["36 ÷ 240 = 0.15", "0.15 = 15%"],
        ),
        (
            replace(_of("15", 240), unknown=Unknown.LEFT),
            "missing-multiply",
            ["?% of 240 = 36 → 36 ÷ 240", "36 ÷ 240 = 0.15", "0.15 = 15%"],
        ),
        (
            replace(_of("15", 240), unknown=Unknown.RIGHT),
            "missing-multiply",
            ["15% of ? = 36 → 36 ÷ 15%", "36 ÷ 15 = 2.4", "2.4 × 100 = 240"],
        ),
    ],
)
def test_worked_example(problem: Problem, best: str, work: list[str]) -> None:
    trick = REGISTRY.best(problem)

    assert trick is not None
    assert trick.id == best
    assert [step.work for step in trick.explain(problem).steps] == work


# Optiver


def test_optiver_mix_includes_percentages() -> None:
    generator = optiver_generator()
    rng = Random(0)

    problems = [generator.generate(rng) for _ in range(600)]
    percent = [p for p in problems if p.left.style is NumberStyle.PERCENT]

    assert len(percent) > 30
    assert Counter(p.unknown for p in percent)[Unknown.LEFT] > 0


def test_percentage_options_are_close_percentages() -> None:
    problem = replace(_of("15", 240), unknown=Unknown.LEFT)

    options = PlausibleChoices().choices(problem, Random(0))

    assert all(str(option).endswith("%") for option in options)
    assert sum(problem.is_correct(option.value) for option in options) == 1
