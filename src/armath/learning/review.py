"""After a session: which problems were slow, and how to solve them faster."""

from dataclasses import dataclass
from random import Random

from armath.domain import Operation, Problem, SessionRecord
from armath.tricks import Explanation, Trick, TrickRegistry


@dataclass(frozen=True)
class StepText:
    label: str
    work: str


@dataclass(frozen=True)
class TrickLesson:
    """A trick applied to one problem, ready to show."""

    trick_id: str
    trick_name: str
    summary: str
    is_general: bool
    problem: str
    steps: tuple[StepText, ...]

    @classmethod
    def of(cls, trick: Trick, explanation: Explanation) -> "TrickLesson":
        return cls(
            trick_id=trick.id,
            trick_name=trick.name,
            summary=trick.summary,
            is_general=trick.fallback,
            problem=explanation.problem.prompt,
            steps=tuple(StepText(step.label, step.work) for step in explanation.steps),
        )


@dataclass(frozen=True)
class ReviewItem:
    equation: str
    seconds: float
    corrections: int
    lesson: TrickLesson | None


def review(record: SessionRecord, registry: TrickRegistry, count: int = 5) -> list[ReviewItem]:
    """The ``count`` slowest problems, each with the best trick for it."""
    slowest = sorted(record.attempts, key=lambda attempt: attempt.elapsed_seconds, reverse=True)
    return [
        ReviewItem(
            equation=attempt.problem.equation,
            seconds=attempt.elapsed_seconds,
            corrections=attempt.corrections,
            lesson=lesson_for(attempt.problem, registry),
        )
        for attempt in slowest[:count]
    ]


def lesson_for(problem: Problem, registry: TrickRegistry) -> TrickLesson | None:
    trick = registry.best(problem)
    return None if trick is None else TrickLesson.of(trick, trick.explain(problem))


@dataclass(frozen=True)
class LibraryEntry:
    trick_id: str
    name: str
    summary: str
    operation: Operation
    is_general: bool
    example: TrickLesson


def library(registry: TrickRegistry) -> list[LibraryEntry]:
    """Every trick with a worked example; examples are stable between visits."""
    entries = []
    for trick in registry.all():
        example = trick.generate(Random(trick.id))
        entries.append(
            LibraryEntry(
                trick_id=trick.id,
                name=trick.name,
                summary=trick.summary,
                operation=trick.operation,
                is_general=trick.fallback,
                example=TrickLesson.of(trick, trick.explain(example)),
            )
        )
    return entries
