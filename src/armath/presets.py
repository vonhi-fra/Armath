"""Ready-made session plans for known interview tests."""

from datetime import timedelta

from armath.generators import ZetamacSettings, zetamac_generator
from armath.modes import CorrectCount, SessionPlan, UntilCorrect

ZETAMAC_DURATION = timedelta(seconds=120)


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
