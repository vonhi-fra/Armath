"""Problems in the style of arithmetic.zetamac.com."""

from dataclasses import dataclass, field

from armath.domain import Operation
from armath.generators.arithmetic import InverseGenerator, MixedGenerator, RangeGenerator
from armath.generators.base import ProblemGenerator
from armath.generators.ranges import IntRange

TWO_TO_HUNDRED = IntRange(2, 100)
TWO_TO_TWELVE = IntRange(2, 12)


@dataclass(frozen=True)
class ZetamacSettings:
    """Zetamac's options; subtraction and division reuse the addition and multiplication ranges.

    Defaults match the site: (2..100) + (2..100) and (2..12) × (2..100).
    """

    addition_left: IntRange = TWO_TO_HUNDRED
    addition_right: IntRange = TWO_TO_HUNDRED
    multiplication_left: IntRange = TWO_TO_TWELVE
    multiplication_right: IntRange = TWO_TO_HUNDRED
    operations: frozenset[Operation] = field(default_factory=lambda: frozenset(Operation))

    def __post_init__(self) -> None:
        if not self.operations:
            raise ValueError("at least one operation must be enabled")
        if Operation.DIVIDE in self.operations and 0 in self.multiplication_left:
            raise ValueError("division needs a multiplication range without 0 for the divisor")


def zetamac_generator(settings: ZetamacSettings) -> ProblemGenerator:
    addition = RangeGenerator(Operation.ADD, settings.addition_left, settings.addition_right)
    multiplication = RangeGenerator(
        Operation.MULTIPLY, settings.multiplication_left, settings.multiplication_right
    )
    by_operation: dict[Operation, ProblemGenerator] = {
        Operation.ADD: addition,
        Operation.SUBTRACT: InverseGenerator(addition),
        Operation.MULTIPLY: multiplication,
        Operation.DIVIDE: InverseGenerator(multiplication),
    }
    return MixedGenerator([by_operation[op] for op in Operation if op in settings.operations])
