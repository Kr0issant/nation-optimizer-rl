import pytest

from core.reward import compute_reward


def test_reward_includes_prosperity() -> None:
    reward = compute_reward(prosperity=12.5)

    assert reward.base_reward == 12.5


def test_productivity_bonus_formula() -> None:
    reward = compute_reward(prosperity=0, productivity=1.5)

    assert reward.productivity_bonus == 25


def test_survival_bonus_formula() -> None:
    reward = compute_reward(prosperity=0, rounds_survived=7)

    assert reward.survival_bonus == 70


def test_under_and_over_penalties() -> None:
    reward = compute_reward(
        prosperity=0,
        over_allocated_count=2,
        under_allocated_count=3,
    )

    assert reward.over_allocation_penalty == -10
    assert reward.under_allocation_penalty == -30


def test_critical_penalty() -> None:
    reward = compute_reward(prosperity=0, critical_failure_occurred=True)

    assert reward.critical_penalty == -1000


def test_total_equals_component_sum() -> None:
    reward = compute_reward(
        prosperity=1,
        productivity=1.2,
        rounds_survived=3,
        over_allocated_count=1,
        under_allocated_count=2,
        critical_failure_occurred=True,
    )

    assert reward.total == pytest.approx(
        reward.base_reward
        + reward.productivity_bonus
        + reward.survival_bonus
        + reward.over_allocation_penalty
        + reward.under_allocation_penalty
        + reward.critical_penalty
    )
