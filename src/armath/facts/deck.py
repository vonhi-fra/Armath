"""Facts worth knowing by heart, grouped into decks."""

from dataclasses import dataclass
from math import gcd
from random import Random

from armath.domain import NumberStyle, Operand, Operation, Problem


def fact_key(problem: Problem) -> str:
    """The same key for ``7 × 8`` and ``8 × 7``; memory is kept per key."""
    left, right = problem.left, problem.right
    if problem.operation is Operation.MULTIPLY and left.value > right.value:
        left, right = right, left
    return f"{left} {problem.operation.symbol} {right}"


@dataclass(frozen=True)
class Fact:
    left: int
    operation: Operation
    right: int
    result_style: NumberStyle | None = None

    @property
    def key(self) -> str:
        return fact_key(self.problem())

    def problem(self, rng: Random | None = None) -> Problem:
        """The fact as a problem; multiplication facts come in either order."""
        left, right = self.left, self.right
        if self.operation is Operation.MULTIPLY and rng is not None and rng.random() < 0.5:
            left, right = right, left
        return Problem.create(
            Operand.integer(left),
            self.operation,
            Operand.integer(right),
            result_style=self.result_style,
        )


@dataclass(frozen=True)
class Deck:
    id: str
    name: str
    description: str
    facts: tuple[Fact, ...]
    """In learning order: new facts are introduced from the front."""
    grid: tuple[int, int] | None = None
    """For times tables, the factor range to draw as a grid."""


def times_tables(limit: int) -> Deck:
    # Easiest first: 2×2, 2×3, 3×3, 2×4, …, so each new fact builds on known ones.
    facts = tuple(
        Fact(small, Operation.MULTIPLY, big)
        for big in range(2, limit + 1)
        for small in range(2, big + 1)
    )
    return Deck(
        id=f"tables-{limit}",
        name=f"Times tables to {limit}",
        description=f"Every product from 2 × 2 to {limit} × {limit}.",
        facts=facts,
        grid=(2, limit),
    )


def squares(low: int = 11, high: int = 25) -> Deck:
    return Deck(
        id="squares",
        name=f"Squares {low} to {high}",
        description="Squares beyond the times table, useful for difference-of-squares tricks.",
        facts=tuple(Fact(n, Operation.MULTIPLY, n) for n in range(low, high + 1)),
    )


def fraction_decimals(denominators: tuple[int, ...] = (2, 4, 5, 8, 16, 20, 25)) -> Deck:
    facts = tuple(
        Fact(top, Operation.DIVIDE, bottom, NumberStyle.DECIMAL)
        for bottom in denominators
        for top in range(1, bottom)
        if gcd(top, bottom) == 1
    )
    return Deck(
        id="fractions",
        name="Fractions as decimals",
        description="3 ÷ 8 = 0.375 and friends: the fractions whose decimals end.",
        facts=facts,
    )


DECKS: tuple[Deck, ...] = (
    times_tables(12),
    times_tables(19),
    squares(),
    fraction_decimals(),
)


def deck_by_id(deck_id: str) -> Deck:
    """Raises ``KeyError`` for an unknown deck."""
    for deck in DECKS:
        if deck.id == deck_id:
            return deck
    raise KeyError(deck_id)
