import pytest

from core.config import CRITICAL_RATIO, SURPLUS_RATIO, WASTAGE_RATIO
from core.sector import Sector


def test_demand_scales_with_baseline_population_and_event_multiplier() -> None:
    sector = Sector(name="Health", baseline=90, event_multiplier=1.5)

    assert sector.demand(2_000_000) == pytest.approx(270)


def test_thresholds_use_configured_ratios() -> None:
    sector = Sector(name="Defense", baseline=100)

    demand = sector.demand(1_000_000)

    assert sector.critical(1_000_000) == pytest.approx(demand * CRITICAL_RATIO)
    assert sector.surplus(1_000_000) == pytest.approx(demand * SURPLUS_RATIO)
    assert sector.wastage(1_000_000) == pytest.approx(demand * WASTAGE_RATIO)


def test_revenue_computation_stores_revenue_factor_and_revenue() -> None:
    sector = Sector(name="Defense", baseline=100)
    sector.allocate(150)

    revenue = sector.compute_revenue(population=1_000_000, productivity=1.2)

    assert sector.revenue_factor_value == pytest.approx(1.8)
    assert sector.revenue == pytest.approx(150 * 1.8 * 1.2)
    assert revenue == sector.revenue


def test_allocation_below_critical_is_critical_failure() -> None:
    sector = Sector(name="Defense", baseline=100)
    sector.allocate(39)

    assert sector.is_critical_failure(1_000_000)
