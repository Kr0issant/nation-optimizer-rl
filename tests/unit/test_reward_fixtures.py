from __future__ import annotations

import pytest

from core.reward import RewardBreakdown, compute_reward
from tests.fixtures.economy_scenarios import evaluate_economy_scenario
from tests.fixtures.reward_scenarios import (
    CRITICAL_FAILURE_REWARD,
    NORMAL_PROFIT_ZONE_REWARD,
    REWARD_SCENARIOS,
    RewardScenario,
)


def _compute_fixture_reward(scenario: RewardScenario) -> RewardBreakdown:
    economy = evaluate_economy_scenario(scenario.economy)
    return compute_reward(
        total_revenue=economy.total_revenue,
        population=scenario.population,
        productivity=scenario.productivity,
        rounds_survived=scenario.rounds_survived,
        over_allocated_count=economy.over_allocated_count,
        under_allocated_count=economy.under_allocated_count,
        critical_failure_occurred=economy.critical_failure,
    )


@pytest.mark.parametrize(
    "scenario",
    REWARD_SCENARIOS,
    ids=[scenario.name for scenario in REWARD_SCENARIOS],
)
def test_reward_scenario_matches_expected_breakdown(
    scenario: RewardScenario,
) -> None:
    reward = _compute_fixture_reward(scenario)

    assert reward.base_reward == pytest.approx(scenario.expected.base_reward)
    assert reward.productivity_bonus == pytest.approx(
        scenario.expected.productivity_bonus,
    )
    assert reward.survival_bonus == pytest.approx(scenario.expected.survival_bonus)
    assert reward.over_allocation_penalty == pytest.approx(
        scenario.expected.over_allocation_penalty,
    )
    assert reward.under_allocation_penalty == pytest.approx(
        scenario.expected.under_allocation_penalty,
    )
    assert reward.critical_penalty == pytest.approx(
        scenario.expected.critical_penalty,
    )
    assert reward.total == pytest.approx(scenario.expected.total)


def test_profit_zone_reward_has_no_allocation_penalties() -> None:
    reward = _compute_fixture_reward(NORMAL_PROFIT_ZONE_REWARD)

    assert reward.over_allocation_penalty == 0.0
    assert reward.under_allocation_penalty == 0.0
    assert reward.critical_penalty == 0.0


def test_critical_failure_reward_applies_critical_penalty() -> None:
    reward = _compute_fixture_reward(CRITICAL_FAILURE_REWARD)

    assert reward.critical_penalty == -1000.0
    assert reward.total == pytest.approx(-983.0922442210181)
