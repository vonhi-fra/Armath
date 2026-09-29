"""Ready-made session plans for known interview tests."""

from datetime import timedelta

from armath.generators import ZetamacSettings, zetamac_generator
from armath.modes import CorrectCount, SessionPlan, UntilCorrect

ZETAMAC_DURATION = timedelta(seconds=120)


def zetamac(
    settings: ZetamacSettings | None = None, duration: timedelta = ZETAMAC_DURATION
) -> SessionPlan:
    """Zetamac: typed answers, auto-advance on the correct answer, one point each."""
    return SessionPlan(
        generator=zetamac_generator(settings or ZetamacSettings()),
        scoring=CorrectCount(),
        answering=UntilCorrect(),
        time_limit=duration,
    )
