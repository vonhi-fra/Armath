"""Small text formatting helpers shared by presenters."""

import math
from datetime import timedelta


def format_clock(remaining: timedelta) -> str:
    """Whole seconds left, rounded up, as ``m:ss`` (so ``0:01`` shows until time is really up)."""
    seconds = max(math.ceil(remaining.total_seconds()), 0)
    return f"{seconds // 60}:{seconds % 60:02d}"
