"""The interface every problem source implements."""

from random import Random
from typing import Protocol

from armath.domain import Problem


class ProblemGenerator(Protocol):
    """Produces problems; all randomness comes from the given ``rng``."""

    def generate(self, rng: Random) -> Problem: ...
