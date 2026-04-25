from __future__ import annotations

from dataclasses import dataclass

from core.config import (
    BASELINE_TAX,
    INITIAL_POPULATION,
    INITIAL_PRODUCTIVITY,
    INITIAL_TREASURY,
    PRODUCTIVITY_STEP,
)
from core.revenue import calculate_revenue, compute_thresholds, revenue_factor


SECTOR_BASELINES: dict[str, float] = {
    "Social": 60.0,
    "Agriculture": 70.0,
    "Health": 90.0,
    "Education": 80.0,
    "Defense": 100.0,
    "Commerce": 75.0,
}

BASE_THRESHOLDS: dict[str, tuple[float, float, float, float]] = {
    "Social": (24.0, 60.0, 90.0, 150.0),
    "Agriculture": (28.0, 70.0, 105.0, 175.0),
    "Health": (36.0, 90.0, 135.0, 225.0),
    "Education": (32.0, 80.0, 120.0, 200.0),
    "Defense": (40.0, 100.0, 150.0, 250.0),
    "Commerce": (30.0, 75.0, 112.5, 187.5),
}

NORMAL_PROFIT_ZONE_REVENUE_FACTOR = 1.8
CONSERVATIVE_REVENUE_FACTOR = 1.0
HEALTH_UNDERFUNDED_REVENUE_FACTOR = 1.0 / 3.0
COMMERCE_WASTAGE_REVENUE_FACTOR = 0.7453559924999299


@dataclass(frozen=True)
class EconomyScenario:
    name: str
    allocations: dict[str, float]
    expected_thresholds: dict[str, tuple[float, float, float, float]]
    expected_revenue_factors: dict[str, float | None]
    expected_revenues: dict[str, float]
    expected_total_allocation: float
    expected_total_consumption: float
    expected_surplus_returned: float
    expected_total_revenue: float
    expected_treasury_after_round: float
    expected_under_allocated_count: int
    expected_over_allocated_count: int
    expected_critical_failure: bool
    expected_average_revenue_factor: float | None
    expected_productivity_after_round: float


@dataclass(frozen=True)
class EconomyEvaluation:
    thresholds: dict[str, tuple[float, float, float, float]]
    revenue_factors: dict[str, float | None]
    revenues: dict[str, float]
    total_allocation: float
    total_consumption: float
    surplus_returned: float
    total_revenue: float
    treasury_after_round: float
    under_allocated_count: int
    over_allocated_count: int
    critical_failure: bool
    average_revenue_factor: float | None
    productivity_after_round: float


NORMAL_PROFIT_ZONE = EconomyScenario(
    name="normal_profit_zone",
    allocations={
        "Social": 90.0,
        "Agriculture": 105.0,
        "Health": 135.0,
        "Education": 120.0,
        "Defense": 150.0,
        "Commerce": 112.5,
    },
    expected_thresholds=BASE_THRESHOLDS,
    expected_revenue_factors={
        "Social": NORMAL_PROFIT_ZONE_REVENUE_FACTOR,
        "Agriculture": NORMAL_PROFIT_ZONE_REVENUE_FACTOR,
        "Health": NORMAL_PROFIT_ZONE_REVENUE_FACTOR,
        "Education": NORMAL_PROFIT_ZONE_REVENUE_FACTOR,
        "Defense": NORMAL_PROFIT_ZONE_REVENUE_FACTOR,
        "Commerce": NORMAL_PROFIT_ZONE_REVENUE_FACTOR,
    },
    expected_revenues={
        "Social": 162.0,
        "Agriculture": 189.0,
        "Health": 243.0,
        "Education": 216.0,
        "Defense": 270.0,
        "Commerce": 202.5,
    },
    expected_total_allocation=712.5,
    expected_total_consumption=475.0,
    expected_surplus_returned=237.5,
    expected_total_revenue=1282.5,
    expected_treasury_after_round=1907.5,
    expected_under_allocated_count=0,
    expected_over_allocated_count=0,
    expected_critical_failure=False,
    expected_average_revenue_factor=1.8,
    expected_productivity_after_round=1.04,
)

CONSERVATIVE_DEMAND = EconomyScenario(
    name="conservative_demand",
    allocations={
        "Social": 60.0,
        "Agriculture": 70.0,
        "Health": 90.0,
        "Education": 80.0,
        "Defense": 100.0,
        "Commerce": 75.0,
    },
    expected_thresholds=BASE_THRESHOLDS,
    expected_revenue_factors={
        "Social": CONSERVATIVE_REVENUE_FACTOR,
        "Agriculture": CONSERVATIVE_REVENUE_FACTOR,
        "Health": CONSERVATIVE_REVENUE_FACTOR,
        "Education": CONSERVATIVE_REVENUE_FACTOR,
        "Defense": CONSERVATIVE_REVENUE_FACTOR,
        "Commerce": CONSERVATIVE_REVENUE_FACTOR,
    },
    expected_revenues={
        "Social": 60.0,
        "Agriculture": 70.0,
        "Health": 90.0,
        "Education": 80.0,
        "Defense": 100.0,
        "Commerce": 75.0,
    },
    expected_total_allocation=475.0,
    expected_total_consumption=475.0,
    expected_surplus_returned=0.0,
    expected_total_revenue=475.0,
    expected_treasury_after_round=1100.0,
    expected_under_allocated_count=0,
    expected_over_allocated_count=0,
    expected_critical_failure=False,
    expected_average_revenue_factor=1.0,
    expected_productivity_after_round=1.0,
)

UNDERFUNDED_SURVIVABLE = EconomyScenario(
    name="underfunded_survivable",
    allocations={
        "Social": 60.0,
        "Agriculture": 70.0,
        "Health": 54.0,
        "Education": 80.0,
        "Defense": 100.0,
        "Commerce": 75.0,
    },
    expected_thresholds=BASE_THRESHOLDS,
    expected_revenue_factors={
        "Social": CONSERVATIVE_REVENUE_FACTOR,
        "Agriculture": CONSERVATIVE_REVENUE_FACTOR,
        "Health": HEALTH_UNDERFUNDED_REVENUE_FACTOR,
        "Education": CONSERVATIVE_REVENUE_FACTOR,
        "Defense": CONSERVATIVE_REVENUE_FACTOR,
        "Commerce": CONSERVATIVE_REVENUE_FACTOR,
    },
    expected_revenues={
        "Social": 60.0,
        "Agriculture": 70.0,
        "Health": 18.0,
        "Education": 80.0,
        "Defense": 100.0,
        "Commerce": 75.0,
    },
    expected_total_allocation=439.0,
    expected_total_consumption=439.0,
    expected_surplus_returned=0.0,
    expected_total_revenue=403.0,
    expected_treasury_after_round=1064.0,
    expected_under_allocated_count=1,
    expected_over_allocated_count=0,
    expected_critical_failure=False,
    expected_average_revenue_factor=8.0 / 9.0,
    expected_productivity_after_round=0.9944444444444445,
)

CRITICAL_FAILURE = EconomyScenario(
    name="critical_failure",
    allocations={
        "Social": 60.0,
        "Agriculture": 70.0,
        "Health": 90.0,
        "Education": 80.0,
        "Defense": 30.0,
        "Commerce": 75.0,
    },
    expected_thresholds=BASE_THRESHOLDS,
    expected_revenue_factors={
        "Social": CONSERVATIVE_REVENUE_FACTOR,
        "Agriculture": CONSERVATIVE_REVENUE_FACTOR,
        "Health": CONSERVATIVE_REVENUE_FACTOR,
        "Education": CONSERVATIVE_REVENUE_FACTOR,
        "Defense": None,
        "Commerce": CONSERVATIVE_REVENUE_FACTOR,
    },
    expected_revenues={
        "Social": 0.0,
        "Agriculture": 0.0,
        "Health": 0.0,
        "Education": 0.0,
        "Defense": 0.0,
        "Commerce": 0.0,
    },
    expected_total_allocation=405.0,
    expected_total_consumption=0.0,
    expected_surplus_returned=0.0,
    expected_total_revenue=0.0,
    expected_treasury_after_round=1000.0,
    expected_under_allocated_count=0,
    expected_over_allocated_count=0,
    expected_critical_failure=True,
    expected_average_revenue_factor=None,
    expected_productivity_after_round=1.0,
)

WASTAGE = EconomyScenario(
    name="wastage",
    allocations={
        "Social": 60.0,
        "Agriculture": 70.0,
        "Health": 90.0,
        "Education": 80.0,
        "Defense": 100.0,
        "Commerce": 225.0,
    },
    expected_thresholds=BASE_THRESHOLDS,
    expected_revenue_factors={
        "Social": CONSERVATIVE_REVENUE_FACTOR,
        "Agriculture": CONSERVATIVE_REVENUE_FACTOR,
        "Health": CONSERVATIVE_REVENUE_FACTOR,
        "Education": CONSERVATIVE_REVENUE_FACTOR,
        "Defense": CONSERVATIVE_REVENUE_FACTOR,
        "Commerce": COMMERCE_WASTAGE_REVENUE_FACTOR,
    },
    expected_revenues={
        "Social": 60.0,
        "Agriculture": 70.0,
        "Health": 90.0,
        "Education": 80.0,
        "Defense": 100.0,
        "Commerce": 167.70509831248424,
    },
    expected_total_allocation=625.0,
    expected_total_consumption=475.0,
    expected_surplus_returned=150.0,
    expected_total_revenue=567.7050983124842,
    expected_treasury_after_round=1192.7050983124842,
    expected_under_allocated_count=0,
    expected_over_allocated_count=1,
    expected_critical_failure=False,
    expected_average_revenue_factor=0.9575593320833217,
    expected_productivity_after_round=0.9978779666041661,
)

ECONOMY_SCENARIOS: tuple[EconomyScenario, ...] = (
    NORMAL_PROFIT_ZONE,
    CONSERVATIVE_DEMAND,
    UNDERFUNDED_SURVIVABLE,
    CRITICAL_FAILURE,
    WASTAGE,
)


def evaluate_economy_scenario(scenario: EconomyScenario) -> EconomyEvaluation:
    thresholds: dict[str, tuple[float, float, float, float]] = {}
    revenue_factors: dict[str, float | None] = {}
    under_allocated_count = 0
    over_allocated_count = 0

    for sector_name, baseline in SECTOR_BASELINES.items():
        sector_thresholds = compute_thresholds(
            baseline=baseline,
            population=INITIAL_POPULATION,
            pop_0=INITIAL_POPULATION,
            event_multiplier=1.0,
        )
        thresholds[sector_name] = sector_thresholds

        critical, demand, surplus, wastage = sector_thresholds
        allocation = scenario.allocations[sector_name]
        factor = revenue_factor(allocation, critical, demand, surplus, wastage)
        revenue_factors[sector_name] = factor

        if factor is None:
            continue
        if allocation < demand:
            under_allocated_count += 1
        elif allocation > surplus:
            over_allocated_count += 1

    critical_failure = any(factor is None for factor in revenue_factors.values())
    total_allocation = sum(scenario.allocations.values())

    if critical_failure:
        revenues = {sector_name: 0.0 for sector_name in SECTOR_BASELINES}
        total_consumption = 0.0
        surplus_returned = 0.0
        total_revenue = 0.0
        average_revenue_factor = None
        productivity_after_round = INITIAL_PRODUCTIVITY
        treasury_after_round = float(INITIAL_TREASURY)
    else:
        revenues = {}
        for sector_name, allocation in scenario.allocations.items():
            critical, demand, surplus, wastage = thresholds[sector_name]
            revenue = calculate_revenue(
                allocation=allocation,
                critical=critical,
                demand=demand,
                surplus=surplus,
                wastage=wastage,
                productivity=INITIAL_PRODUCTIVITY,
            )
            revenues[sector_name] = revenue or 0.0

        total_consumption = sum(
            min(scenario.allocations[sector_name], thresholds[sector_name][1])
            for sector_name in scenario.allocations
        )
        surplus_returned = total_allocation - total_consumption
        total_revenue = sum(revenues.values())
        viable_factors = [factor for factor in revenue_factors.values() if factor is not None]
        average_revenue_factor = sum(viable_factors) / len(viable_factors)
        productivity_after_round = (
            INITIAL_PRODUCTIVITY
            + PRODUCTIVITY_STEP * (average_revenue_factor - 1.0)
        )
        treasury_after_round = (
            INITIAL_TREASURY
            + BASELINE_TAX
            + total_revenue
            - total_consumption
        )

    return EconomyEvaluation(
        thresholds=thresholds,
        revenue_factors=revenue_factors,
        revenues=revenues,
        total_allocation=total_allocation,
        total_consumption=total_consumption,
        surplus_returned=surplus_returned,
        total_revenue=total_revenue,
        treasury_after_round=treasury_after_round,
        under_allocated_count=under_allocated_count,
        over_allocated_count=over_allocated_count,
        critical_failure=critical_failure,
        average_revenue_factor=average_revenue_factor,
        productivity_after_round=productivity_after_round,
    )
