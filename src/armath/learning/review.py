"""After a session: which problems were slow, and how to solve them faster."""

from dataclasses import dataclass
from random import Random

from armath.domain import Attempt, Operand, Operation, Problem, SessionRecord
from armath.domain.numbers import can_write, infer_style
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
    wrong_answer: str | None = None
    """What the user answered, if it was wrong (multiple-choice sessions)."""


def review(record: SessionRecord, registry: TrickRegistry, count: int = 5) -> list[ReviewItem]:
    """Wrong answers first (they cost points), then the slowest; each with its best trick."""
    ordered = sorted(
        record.attempts, key=lambda attempt: (attempt.is_correct, -attempt.elapsed_seconds)
    )
    return [
        ReviewItem(
            equation=attempt.problem.equation,
            seconds=attempt.elapsed_seconds,
            corrections=attempt.corrections,
            lesson=lesson_for(attempt.problem, registry),
            wrong_answer=None if attempt.is_correct else _as_answer(attempt),
        )
        for attempt in ordered[:count]
    ]


def _as_answer(attempt: Attempt) -> str:
    """The response written like the answer would be (e.g. ``0.5`` rather than ``1/2``)."""
    style = attempt.problem.answer.style
    value = attempt.response
    return str(
        Operand(value, style) if can_write(value, style) else Operand(value, infer_style(value))
    )


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
