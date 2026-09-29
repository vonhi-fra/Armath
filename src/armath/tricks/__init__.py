"""Mental arithmetic tricks: when they apply, how they work, and practice problems for them."""

from armath.tricks.base import Trick, WholeNumberTrick
from armath.tricks.catalogue import default_registry
from armath.tricks.explanation import Explanation, Step, calc
from armath.tricks.registry import TrickRegistry

__all__ = [
    "Explanation",
    "Step",
    "Trick",
    "TrickRegistry",
    "WholeNumberTrick",
    "calc",
    "default_registry",
]
