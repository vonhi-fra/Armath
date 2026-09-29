"""A running practice session: shows problems, records attempts, keeps time and score."""

from dataclasses import dataclass
from datetime import timedelta
from fractions import Fraction
from random import Random

from armath.domain import Attempt, Problem, parse_answer
from armath.generators import ProblemGenerator
from armath.modes.answering import AnswerPolicy
from armath.modes.clock import Clock
from armath.modes.scoring import ScoringPolicy


@dataclass(frozen=True)
class SessionPlan:
    """Everything that defines a kind of session; presets are just named plans."""

    generator: ProblemGenerator
    scoring: ScoringPolicy
    answering: AnswerPolicy
    time_limit: timedelta | None = None
    question_limit: int | None = None

    def __post_init__(self) -> None:
        if self.time_limit is None and self.question_limit is None:
            raise ValueError("a session needs a time limit, a question limit or both")
        if self.time_limit is not None and self.time_limit <= timedelta(0):
            raise ValueError("time limit must be positive")
        if self.question_limit is not None and self.question_limit <= 0:
            raise ValueError("question limit must be positive")


class SessionOverError(RuntimeError):
    """Raised when answering after the session has ended."""


class Session:
    """Starts on creation and shows the first problem immediately."""

    def __init__(self, plan: SessionPlan, clock: Clock, rng: Random) -> None:
        self._plan = plan
        self._clock = clock
        self._rng = rng
        self._started_at = clock.now()
        self._shown_at = self._started_at
        self._current = plan.generator.generate(rng)
        self._attempts: list[Attempt] = []

    @property
    def current(self) -> Problem:
        return self._current

    @property
    def attempts(self) -> tuple[Attempt, ...]:
        return tuple(self._attempts)

    @property
    def score(self) -> int:
        return self._plan.scoring.score(self._attempts)

    @property
    def elapsed(self) -> timedelta:
        return self._clock.now() - self._started_at

    @property
    def remaining_time(self) -> timedelta | None:
        if self._plan.time_limit is None:
            return None
        return max(self._plan.time_limit - self.elapsed, timedelta(0))

    @property
    def is_over(self) -> bool:
        out_of_time = self.remaining_time == timedelta(0)
        limit = self._plan.question_limit
        out_of_questions = limit is not None and len(self._attempts) >= limit
        return out_of_time or out_of_questions

    def answer(self, text: str) -> Attempt | None:
        """Submit typed text; returns the attempt if it was accepted, else ``None``."""
        response = parse_answer(text)
        if response is None:
            self._ensure_running()
            return None
        return self.answer_value(response)

    def answer_value(self, response: Fraction) -> Attempt | None:
        """Submit an exact value (e.g. a multiple-choice option)."""
        self._ensure_running()
        if not self._plan.answering.accepts(self._current, response):
            return None
        now = self._clock.now()
        attempt = Attempt(
            problem=self._current,
            response=response,
            elapsed_seconds=(now - self._shown_at).total_seconds(),
            answered_at=now,
        )
        self._attempts.append(attempt)
        self._current = self._plan.generator.generate(self._rng)
        self._shown_at = now
        return attempt

    def _ensure_running(self) -> None:
        if self.is_over:
            raise SessionOverError("the session is over")
