from random import Random

import pytest
from factories import attempt, record

from armath.domain import Operand, Operation, Problem
from armath.generators import FilteredGenerator, RangeGenerator
from armath.generators.ranges import IntRange
from armath.learning import Drill, DrillGenerator, DrillSettings, lookalikes_for
from armath.learning.drill import NearMissGenerator
from armath.tricks import Trick, WholeNumberTrick, default_registry

REGISTRY = default_registry()
TIMES_ELEVEN = REGISTRY.get("mul-11")


def test_focused_round_only_uses_the_trick() -> None:
    generator = DrillGenerator(
        TIMES_ELEVEN, lookalikes_for(TIMES_ELEVEN), DrillSettings(focused=30, mixed=0)
    )
    rng = Random(0)

    assert all(TIMES_ELEVEN.applies_to(generator.generate(rng)) for _ in range(30))


def test_mixed_round_includes_lookalikes_of_the_same_operation() -> None:
    generator = DrillGenerator(
        TIMES_ELEVEN, lookalikes_for(TIMES_ELEVEN), DrillSettings(focused=0, mixed=200)
    )
    rng = Random(0)

    problems = [generator.generate(rng) for _ in range(200)]

    assert all(p.operation is Operation.MULTIPLY for p in problems)
    with_trick = sum(TIMES_ELEVEN.applies_to(p) for p in problems)
    assert 60 < with_trick < 140


@pytest.mark.parametrize(
    "trick",
    [t for t in REGISTRY.all() if isinstance(t, WholeNumberTrick) and not t.fallback],
    ids=lambda trick: trick.id,
)
def test_near_misses_look_like_the_trick_but_it_does_not_apply(trick: Trick) -> None:
    lookalikes = lookalikes_for(trick)
    assert lookalikes is not None
    generator = NearMissGenerator(trick, fallback=lookalikes)
    rng = Random(0)

    for _ in range(30):
        problem = generator.generate(rng)
        assert problem.operation is trick.operation
        assert not trick.applies_to(problem)
        assert problem.answer.value.denominator == 1


def test_near_misses_of_times_eleven_change_one_number_slightly() -> None:
    never = FilteredGenerator(TIMES_ELEVEN, lambda problem: False, max_tries=1)
    generator = NearMissGenerator(TIMES_ELEVEN, fallback=never)  # fallback would raise
    rng = Random(3)

    factors = [generator.generate(rng) for _ in range(40)]

    assert all(9 <= p.left.value <= 13 and p.left.value != 11 for p in factors)


def test_general_methods_have_no_lookalikes() -> None:
    assert lookalikes_for(REGISTRY.get("mul-split")) is None


def test_drill_plan_is_fresh_each_time() -> None:
    drill = Drill(TIMES_ELEVEN, REGISTRY)

    assert drill.plan().generator is not drill.plan().generator
    assert drill.plan().question_limit == 20
    assert drill.plan().name == "Drill: ×11: digit sum in the middle"


def test_hints_fade_after_the_focused_round() -> None:
    drill = Drill(TIMES_ELEVEN, REGISTRY, DrillSettings(focused=2, mixed=2))

    assert drill.hint(0) == f"{TIMES_ELEVEN.name}: {TIMES_ELEVEN.summary}"
    assert drill.hint(1) is not None
    mixed_hint = drill.hint(2)
    assert mixed_hint is not None
    assert mixed_hint.startswith("Mixed round")


def test_general_method_drill_has_no_mixed_round_hint() -> None:
    drill = Drill(REGISTRY.get("mul-split"), REGISTRY, DrillSettings(focused=1, mixed=1))

    assert drill.hint(1) is None


def test_lesson_prefers_the_drilled_trick() -> None:
    drill = Drill(REGISTRY.get("mul-split"), REGISTRY)
    problem = Problem.create(Operand.integer(11), Operation.MULTIPLY, Operand.integer(35))

    lesson = drill.lesson(problem)

    assert lesson is not None
    assert lesson.trick_id == "mul-split"  # not ×11, which would be "best"


def test_lesson_for_lookalike_uses_the_best_trick() -> None:
    drill = Drill(TIMES_ELEVEN, REGISTRY)
    problem = Problem.create(Operand.integer(9), Operation.MULTIPLY, Operand.integer(35))

    lesson = drill.lesson(problem)

    assert lesson is not None
    assert lesson.trick_id == "mul-9"


def test_report_splits_rounds_and_lookalikes() -> None:
    drill = Drill(TIMES_ELEVEN, REGISTRY, DrillSettings(focused=2, mixed=2))
    eleven = Problem.create(Operand.integer(11), Operation.MULTIPLY, Operand.integer(35))
    other = Problem.create(Operand.integer(7), Operation.MULTIPLY, Operand.integer(35))
    session = record(
        attempt(eleven, seconds=4),
        attempt(eleven, seconds=2),
        attempt(eleven, seconds=1.5, corrections=1),
        attempt(other, seconds=3),
    )

    report = drill.report(session)

    assert report.focused_seconds == 3
    assert report.mixed_trick_seconds == 1.5
    assert report.lookalike_seconds == 3
    assert report.first_try_rate == 0.75


@pytest.mark.parametrize(("focused", "mixed", "share"), [(0, 0, 0.5), (-1, 5, 0.5), (5, 5, 1.5)])
def test_invalid_settings(focused: int, mixed: int, share: float) -> None:
    with pytest.raises(ValueError, match=r"drill|share"):
        DrillSettings(focused=focused, mixed=mixed, trick_share=share)


def test_filtered_generator_gives_up_eventually() -> None:
    small = RangeGenerator(Operation.ADD, IntRange(1, 2), IntRange(1, 2))
    impossible = FilteredGenerator(small, lambda problem: False, max_tries=10)

    with pytest.raises(RuntimeError, match="10 tries"):
        impossible.generate(Random(0))
