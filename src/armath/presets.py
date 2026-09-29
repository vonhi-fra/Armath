"""Ready-made session plans for known interview tests."""

from datetime import timedelta

from armath.generators import ZetamacSettings, optiver_generator, zetamac_generator
from armath.modes import (
    CorrectCount,
    CorrectMinusWrong,
    FirstResponse,
    PlausibleChoices,
    SessionPlan,
    UntilCorrect,
)

ZETAMAC_DURATION = timedelta(seconds=120)
OPTIVER_QUESTIONS = 80
OPTIVER_DURATION = timedelta(minutes=8)
OPTIVER_NAME = "Optiver 80 in 8"


def optiver() -> SessionPlan:
    """Optiver's 80-in-8: 80 multiple-choice questions, 8 minutes, +1 right / −1 wrong."""
    return SessionPlan(
        generator=optiver_generator(),
        scoring=CorrectMinusWrong(),
        answering=FirstResponse(),
        time_limit=OPTIVER_DURATION,
        question_limit=OPTIVER_QUESTIONS,
        name=OPTIVER_NAME,
        choices=PlausibleChoices(),
    )


def zetamac(
    settings: ZetamacSettings | None = None, duration: timedelta = ZETAMAC_DURATION
) -> SessionPlan:
    """Zetamac: typed answers, auto-advance on the correct answer, one point each."""
    settings = settings or ZetamacSettings()
    return SessionPlan(
        generator=zetamac_generator(settings),
        scoring=CorrectCount(),
        answering=UntilCorrect(),
        time_limit=duration,
        name=zetamac_name(settings, duration),
    )


def zetamac_name(settings: ZetamacSettings, duration: timedelta) -> str:
    """E.g. ``Zetamac 120s`` for the default ranges, ``Zetamac 60s custom`` otherwise.

    Scores are only comparable between sessions with the same name.
    """
    name = f"Zetamac {int(duration.total_seconds())}s"
    return name if settings == ZetamacSettings() else f"{name} custom"
