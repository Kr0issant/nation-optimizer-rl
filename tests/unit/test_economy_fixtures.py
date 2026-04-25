from __future__ import annotations

import pytest

from tests.fixtures.economy_scenarios import (
    CONSERVATIVE_DEMAND,
    CRITICAL_FAILURE,
    ECONOMY_SCENARIOS,
    NORMAL_PROFIT_ZONE,
    UNDERFUNDED_SURVIVABLE,
    WASTAGE,
    EconomyScenario,
    evaluate_economy_scenario,
)


def _assert_float_mapping(
    actual: dict[str, float],
    expected: dict[str, float],
) -> None:
    assert actual.keys() == expected.keys()
    for key, expected_value in expected.items():
        assert actual[key] == pytest.approx(expected_value)


def _assert_optional_float_mapping(
    actual: dict[str, float | None],
    expected: dict[str, float | None],
) -> None:
    assert actual.keys() == expected.keys()
    for key, expected_value in expected.items():
        if expected_value is None:
            assert actual[key] is None
        else:
            assert actual[key] == pytest.approx(expected_value)


def _assert_thresholds(
    actual: dict[str, tuple[float, float, float, float]],
    expected: dict[str, tuple[float, float, float, float]],
) -> None:
    assert actual.keys() == expected.keys()
    for key, expected_values in expected.items():
        assert actual[key] == pytest.approx(expected_values)


@pytest.mark.parametrize(
    "scenario",
    ECONOMY_SCENARIOS,
    ids=[scenario.name for scenario in ECONOMY_SCENARIOS],
)
def test_economy_scenario_matches_expected_values(
    scenario: EconomyScenario,
) -> None:
    result = evaluate_economy_scenario(scenario)

    _assert_thresholds(result.thresholds, scenario.expected_thresholds)
    _assert_optional_float_mapping(
        result.revenue_factors,
        scenario.expected_revenue_factors,
    )
    _assert_float_mapping(result.revenues, scenario.expected_revenues)

    assert result.total_allocation == pytest.approx(
        scenario.expected_total_allocation,
    )
    assert result.total_consumption == pytest.approx(
        scenario.expected_total_consumption,
    )
    assert result.surplus_returned == pytest.approx(
        scenario.expected_surplus_returned,
    )
    assert result.total_revenue == pytest.approx(
        scenario.expected_total_revenue,
    )
    assert result.treasury_after_round == pytest.approx(
        scenario.expected_treasury_after_round,
    )
    assert result.under_allocated_count == scenario.expected_under_allocated_count
    assert result.over_allocated_count == scenario.expected_over_allocated_count
    assert result.critical_failure is scenario.expected_critical_failure

    if scenario.expected_average_revenue_factor is None:
        assert result.average_revenue_factor is None
    else:
        assert result.average_revenue_factor == pytest.approx(
            scenario.expected_average_revenue_factor,
        )
    assert result.productivity_after_round == pytest.approx(
        scenario.expected_productivity_after_round,
    )


def test_normal_profit_zone_has_peak_revenue_without_penalties() -> None:
    result = evaluate_economy_scenario(NORMAL_PROFIT_ZONE)

    for factor in result.revenue_factors.values():
        assert factor == pytest.approx(1.8)
    assert result.surplus_returned == pytest.approx(237.5)
    assert result.under_allocated_count == 0
    assert result.over_allocated_count == 0
    assert not result.critical_failure


def test_conservative_demand_round_breaks_even_without_failure() -> None:
    result = evaluate_economy_scenario(CONSERVATIVE_DEMAND)

    for factor in result.revenue_factors.values():
        assert factor == pytest.approx(1.0)
    assert result.total_revenue == pytest.approx(475.0)
    assert not result.critical_failure


def test_underfunded_survivable_round_applies_under_allocation_penalty_zone() -> None:
    result = evaluate_economy_scenario(UNDERFUNDED_SURVIVABLE)

    assert result.revenue_factors["Health"] == pytest.approx(1.0 / 3.0)
    assert result.under_allocated_count == 1
    assert result.over_allocated_count == 0
    assert not result.critical_failure


def test_critical_failure_round_marks_failing_sector_factor_as_none() -> None:
    result = evaluate_economy_scenario(CRITICAL_FAILURE)

    assert result.revenue_factors["Defense"] is None
    assert result.total_revenue == 0.0
    assert result.critical_failure


def test_wastage_round_applies_over_allocation_penalty_zone() -> None:
    result = evaluate_economy_scenario(WASTAGE)

    assert result.revenue_factors["Commerce"] == pytest.approx(0.7453559924999299)
    assert result.surplus_returned == pytest.approx(150.0)
    assert result.under_allocated_count == 0
    assert result.over_allocated_count == 1
    assert not result.critical_failure
