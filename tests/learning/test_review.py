from factories import attempt, problem, record

from armath.domain import Operand, Operation, Problem
from armath.learning import StepText, lesson_for, library, review
from armath.tricks import default_registry

REGISTRY = default_registry()


def test_review_lists_slowest_problems_first_with_their_best_trick() -> None:
    session = record(
        attempt(problem(11, Operation.MULTIPLY, 67), seconds=6, corrections=1),
        attempt(problem(2, Operation.ADD, 3), seconds=1),
        attempt(problem(9, Operation.MULTIPLY, 74), seconds=3),
    )

    items = review(session, REGISTRY, count=2)

    assert [item.equation for item in items] == ["11 × 67 = 737", "9 × 74 = 666"]
    assert items[0].corrections == 1
    assert items[0].lesson is not None
    assert items[0].lesson.trick_id == "mul-11"
    assert items[0].lesson.steps[-1] == StepText(
        "13 has two digits: write 3 in the middle and carry 1 to the 6", "6+1 | 3 | 7 → 737"
    )


def test_problems_without_a_trick_have_no_lesson() -> None:
    negative = Problem.create(Operand.integer(-3), Operation.ADD, Operand.integer(2))

    assert lesson_for(negative, REGISTRY) is None


def test_library_has_a_stable_worked_example_for_every_trick() -> None:
    first, second = library(REGISTRY), library(REGISTRY)

    assert [entry.trick_id for entry in first] == [trick.id for trick in REGISTRY.all()]
    assert first == second
    assert all(entry.example.steps for entry in first)
    assert sum(entry.is_general for entry in first) == sum(t.fallback for t in REGISTRY.all())
