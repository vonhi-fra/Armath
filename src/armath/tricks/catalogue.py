"""The built-in tricks; see docs/research.md §6 for the full catalogue and its sources."""

from armath.tricks.addition import LeftToRightAddition, RoundUpAddition
from armath.tricks.division import (
    ChunkingDivision,
    DivideByEleven,
    DivideByFive,
    DivideByNine,
    HalveBoth,
)
from armath.tricks.multiplication import (
    DoubleRepeatedly,
    HalveAndDouble,
    RoundUpMultiplication,
    SplitMultiplication,
    TimesEleven,
    TimesFive,
    TimesNine,
    TimesQuarterOrHalfHundred,
    TimesTwelve,
)
from armath.tricks.registry import TrickRegistry
from armath.tricks.subtraction import (
    CountUpSubtraction,
    LeftToRightSubtraction,
    RoundUpSubtraction,
)


def default_registry() -> TrickRegistry:
    return TrickRegistry(
        [
            LeftToRightAddition(),
            RoundUpAddition(),
            LeftToRightSubtraction(),
            RoundUpSubtraction(),
            CountUpSubtraction(),
            SplitMultiplication(),
            RoundUpMultiplication(),
            TimesFive(),
            TimesQuarterOrHalfHundred(),
            TimesNine(),
            TimesEleven(),
            TimesTwelve(),
            HalveAndDouble(),
            DoubleRepeatedly(),
            ChunkingDivision(),
            DivideByFive(),
            HalveBoth(),
            DivideByEleven(),
            DivideByNine(),
        ]
    )
