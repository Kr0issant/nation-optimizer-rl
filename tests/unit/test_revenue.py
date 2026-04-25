import pytest

from core.config import RF_MAX
from core.revenue import calculate_revenue, revenue_factor


CRITICAL = 40
DEMAND = 100
SURPLUS = 150
WASTAGE = 250


def test_below_critical_returns_none() -> None:
    assert revenue_factor(39, CRITICAL, DEMAND, SURPLUS, WASTAGE) is None


def test_at_critical_returns_zero() -> None:
    assert revenue_factor(CRITICAL, CRITICAL, DEMAND, SURPLUS, WASTAGE) == 0


def test_at_demand_returns_one() -> None:
    assert revenue_factor(DEMAND, CRITICAL, DEMAND, SURPLUS, WASTAGE) == 1.0


def test_at_surplus_returns_max_revenue_factor() -> None:
    assert revenue_factor(SURPLUS, CRITICAL, DEMAND, SURPLUS, WASTAGE) == RF_MAX


def test_at_wastage_returns_approximately_one() -> None:
    assert revenue_factor(WASTAGE, CRITICAL, DEMAND, SURPLUS, WASTAGE) == pytest.approx(1.0)


def test_beyond_wastage_is_below_one() -> None:
    factor = revenue_factor(300, CRITICAL, DEMAND, SURPLUS, WASTAGE)

    assert factor is not None
    assert factor < 1.0


def test_revenue_equals_allocation_times_factor_times_productivity() -> None:
    allocation = 125
    productivity = 1.2
    factor = revenue_factor(allocation, CRITICAL, DEMAND, SURPLUS, WASTAGE)

    assert calculate_revenue(
        allocation,
        CRITICAL,
        DEMAND,
        SURPLUS,
        WASTAGE,
        productivity,
    ) == pytest.approx(allocation * factor * productivity)
