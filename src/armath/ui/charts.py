"""Chart geometry, computed in pure Python so it can be tested; the DOM only draws it.

Follows the dataviz mark specs: one series, 2px line, 8px markers with a surface ring, clean
y ticks on hairline gridlines, and only the first and last x positions labelled.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

WIDTH = 640
HEIGHT = 220
MARGIN_LEFT = 40
MARGIN_RIGHT = 20
MARGIN_TOP = 14
MARGIN_BOTTOM = 28


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class Tick:
    position: float
    label: str


@dataclass(frozen=True)
class LineChartLayout:
    width: int
    height: int
    left: float
    right: float
    top: float
    bottom: float
    points: tuple[Point, ...]
    y_ticks: tuple[Tick, ...]
    x_tick_indexes: tuple[int, ...]
    """Which points get an x-axis label (the caller formats it, e.g. as a local date)."""

    @property
    def path(self) -> str:
        return " ".join(
            f"{'M' if index == 0 else 'L'}{point.x:.1f},{point.y:.1f}"
            for index, point in enumerate(self.points)
        )

    def nearest_index(self, x: float) -> int:
        """The point closest to a horizontal position (for the hover crosshair)."""
        return min(range(len(self.points)), key=lambda index: abs(self.points[index].x - x))


def nice_ticks(low: float, high: float, target: int = 4) -> list[float]:
    """Round tick values (steps of 1, 2 or 5 × 10ⁿ) covering ``low``..``high``."""
    if high <= low:
        high = low + 1
    raw_step = (high - low) / target
    magnitude = 10 ** math.floor(math.log10(raw_step))
    step = next(m * magnitude for m in (1, 2, 5, 10) if m * magnitude >= raw_step)
    start = math.floor(low / step) * step
    end = math.ceil(high / step) * step
    count = round((end - start) / step)
    return [start + index * step for index in range(count + 1)]


def line_chart(values: Sequence[float]) -> LineChartLayout:
    """Lay out one series, evenly spaced in order; the y axis starts at zero."""
    if not values:
        raise ValueError("a chart needs at least one value")
    left, right = MARGIN_LEFT, WIDTH - MARGIN_RIGHT
    top, bottom = MARGIN_TOP, HEIGHT - MARGIN_BOTTOM
    ticks = nice_ticks(0, max(max(values), 1))
    low, high = ticks[0], ticks[-1]

    def x_at(index: int) -> float:
        if len(values) == 1:
            return (left + right) / 2
        return left + index * (right - left) / (len(values) - 1)

    def y_at(value: float) -> float:
        return bottom - (value - low) / (high - low) * (bottom - top)

    last = len(values) - 1
    return LineChartLayout(
        width=WIDTH,
        height=HEIGHT,
        left=left,
        right=right,
        top=top,
        bottom=bottom,
        points=tuple(Point(x_at(i), y_at(value)) for i, value in enumerate(values)),
        y_ticks=tuple(Tick(y_at(tick), _tick_label(tick)) for tick in ticks),
        x_tick_indexes=(0,) if last == 0 else (0, last),
    )


def _tick_label(value: float) -> str:
    return f"{value:,.0f}" if value == int(value) else f"{value:,g}"
