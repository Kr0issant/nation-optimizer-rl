from core.config import MAX_PRODUCTIVITY, MIN_PRODUCTIVITY
from core.productivity import ProductivityTracker


def test_productivity_increases_when_average_revenue_factor_above_one() -> None:
    tracker = ProductivityTracker()

    assert tracker.update([1.8, 1.4]) > 1.0


def test_productivity_decreases_when_average_revenue_factor_below_one() -> None:
    tracker = ProductivityTracker()

    assert tracker.update([0.5, 0.75]) < 1.0


def test_productivity_clamps_at_minimum() -> None:
    tracker = ProductivityTracker(value=MIN_PRODUCTIVITY)

    assert tracker.update([0.0]) == MIN_PRODUCTIVITY


def test_productivity_clamps_at_maximum() -> None:
    tracker = ProductivityTracker(value=MAX_PRODUCTIVITY)

    assert tracker.update([1.8]) == MAX_PRODUCTIVITY


def test_productivity_unchanged_when_average_revenue_factor_equals_one() -> None:
    tracker = ProductivityTracker(value=1.25)

    assert tracker.update([0.5, 1.5]) == 1.25
