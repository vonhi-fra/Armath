"""The built-in tricks; see docs/research.md §6 for the full catalogue and its sources."""

from armath.domain import Operation
from armath.tricks.addition import LeftToRightAddition, RoundUpAddition
from armath.tricks.base import Trick
from armath.tricks.decimals import DecimalMethod, FriendlyDecimal
from armath.tricks.division import (
    CancelZeros,
    ChunkingDivision,
    DivideByEleven,
    DivideByFive,
    DivideByNine,
    HalveBoth,
)
from armath.tricks.fractions import FractionMethod
from armath.tricks.inverse import MissingOperand
from armath.tricks.multiplication import (
    BaseHundred,
    CloseTogether,
    CrossMultiplication,
    DifferenceOfSquares,
    DoubleRepeatedly,
    HalveAndDouble,
    RoundUpMultiplication,
    SplitMultiplication,
    SquareEndingInFive,
    SquareUpAndDown,
    TeensTimesTeens,
    TimesEleven,
    TimesFive,
    TimesNine,
    TimesQuarterOrHalfHundred,
    TimesTwelve,
    UnitsSumToTen,
)
from armath.tricks.registry import TrickRegistry
from armath.tricks.subtraction import (
    CountUpSubtraction,
    LeftToRightSubtraction,
    RoundUpSubtraction,
)


def _direct_tricks() -> list[Trick]:
    """Tricks for ``a <op> b = ?``, grouped by operation."""
    return [
        LeftToRightAddition(),
        RoundUpAddition(),
        DecimalMethod(Operation.ADD),
        FractionMethod(Operation.ADD),
        LeftToRightSubtraction(),
        RoundUpSubtraction(),
        CountUpSubtraction(),
        DecimalMethod(Operation.SUBTRACT),
        FractionMethod(Operation.SUBTRACT),
        SplitMultiplication(),
        RoundUpMultiplication(),
        TimesFive(),
        TimesQuarterOrHalfHundred(),
        TimesNine(),
        TimesEleven(),
        TimesTwelve(),
        HalveAndDouble(),
        DoubleRepeatedly(),
        DifferenceOfSquares(),
        SquareEndingInFive(),
        UnitsSumToTen(),
        BaseHundred(),
        TeensTimesTeens(),
        CloseTogether(),
        SquareUpAndDown(),
        CrossMultiplication(),
        DecimalMethod(Operation.MULTIPLY),
        FriendlyDecimal(Operation.MULTIPLY),
        FractionMethod(Operation.MULTIPLY),
        ChunkingDivision(),
        DivideByFive(),
        HalveBoth(),
        DivideByEleven(),
        DivideByNine(),
        CancelZeros(),
        DecimalMethod(Operation.DIVIDE),
        FriendlyDecimal(Operation.DIVIDE),
        FractionMethod(Operation.DIVIDE),
    ]


def default_registry() -> TrickRegistry:
    direct = _direct_tricks()
    # Missing-operand tricks rewrite the problem and explain the result with a direct trick.
    solver = TrickRegistry(direct)
    missing = [MissingOperand(operation, solver) for operation in Operation]
    return TrickRegistry(
        sorted([*direct, *missing], key=lambda t: list(Operation).index(t.operation))
    )
