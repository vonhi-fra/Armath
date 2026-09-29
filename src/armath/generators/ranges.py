"""Inclusive integer ranges that operands are drawn from."""

from dataclasses import dataclass
from random import Random


@dataclass(frozen=True)
class IntRange:
    """All integers from ``low`` to ``high``, both included."""

    low: int
    high: int

    def __post_init__(self) -> None:
        if self.low > self.high:
            raise ValueError(f"empty range: {self.low}..{self.high}")

    def __contains__(self, value: int) -> bool:
        return self.low <= value <= self.high

    def sample(self, rng: Random) -> int:
        return rng.randint(self.low, self.high)
