import pytest

from armath.ui.charts import HEIGHT, MARGIN_BOTTOM, MARGIN_TOP, line_chart, nice_ticks


@pytest.mark.parametrize(
    ("low", "high", "ticks"),
    [
        (0, 47, [0, 20, 40, 60]),
        (0, 100, [0, 50, 100]),
        (0, 7, [0, 2, 4, 6, 8]),
        (0, 0, [0, 0.5, 1]),
        (0, 0.3, [0, 0.1, 0.2, 0.3]),
    ],
)
def test_nice_ticks(low: float, high: float, ticks: list[float]) -> None:
    assert nice_ticks(low, high) == pytest.approx(ticks)


def test_points_span_the_plot_and_scale_from_zero() -> None:
    layout = line_chart([0, 30, 60])

    assert [p.x for p in layout.points] == [
        layout.left,
        (layout.left + layout.right) / 2,
        layout.right,
    ]
    assert layout.points[0].y == HEIGHT - MARGIN_BOTTOM
    assert layout.points[2].y == MARGIN_TOP
    assert [tick.label for tick in layout.y_ticks] == ["0", "20", "40", "60"]
    assert layout.x_tick_indexes == (0, 2)
    assert layout.path.startswith("M40.0,")
    assert layout.path.count("L") == 2


def test_single_point_is_centred() -> None:
    layout = line_chart([12])

    assert layout.points[0].x == (layout.left + layout.right) / 2
    assert layout.x_tick_indexes == (0,)


def test_nearest_index_snaps_to_closest_point() -> None:
    layout = line_chart([1, 2, 3, 4])

    assert layout.nearest_index(layout.left - 50) == 0
    assert layout.nearest_index(layout.points[2].x + 3) == 2
    assert layout.nearest_index(layout.right + 50) == 3


def test_empty_series_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least one value"):
        line_chart([])
