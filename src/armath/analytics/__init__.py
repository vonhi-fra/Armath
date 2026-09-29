"""Turning attempts into insight."""

from armath.analytics.features import ProblemKind, kind_of
from armath.analytics.insights import (
    KindInsight,
    TrickInsight,
    kind_insights,
    recent_practice,
    recommendations,
    trick_insights,
)
from armath.analytics.progress import ModeProgress, ScorePoint, mode_progress
from armath.analytics.summary import SessionSummary, first_try_rate, summarize

__all__ = [
    "KindInsight",
    "ModeProgress",
    "ProblemKind",
    "ScorePoint",
    "SessionSummary",
    "TrickInsight",
    "first_try_rate",
    "kind_insights",
    "kind_of",
    "mode_progress",
    "recent_practice",
    "recommendations",
    "summarize",
    "trick_insights",
]
