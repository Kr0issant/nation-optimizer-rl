from __future__ import annotations

from dataclasses import dataclass

from core.config import INITIAL_POPULATION, INITIAL_PRODUCTIVITY

from .economy_scenarios import (
    CONSERVATIVE_DEMAND,
    CRITICAL_FAILURE,
    NORMAL_PROFIT_ZONE,
    UNDERFUNDED_SURVIVABLE,
    WASTAGE,
    EconomyScenario,
)


@dataclass(frozen=True)
class RewardExpectation:
    base_reward: float
    productivity_bonus: float
    survival_bonus: float
    over_allocation_penalty: float
    under_allocation_penalty: float
    critical_penalty: float
    total: float


@dataclass(frozen=True)
class RewardScenario:
    name: str
    economy: EconomyScenario
    population: int
    productivity: float
    rounds_survived: int
    expected: RewardExpectation


NORMAL_PROFIT_ZONE_REWARD = RewardScenario(
    name="normal_profit_zone_reward",
    economy=NORMAL_PROFIT_ZONE,
    population=INITIAL_POPULATION,
    productivity=INITIAL_PRODUCTIVITY,
    rounds_survived=5,
    expected=RewardExpectation(
        base_reward=14.065101779293082,
        productivity_bonus=0.0,
        survival_bonus=50.0,
        over_allocation_penalty=0.0,
        under_allocation_penalty=0.0,
        critical_penalty=0.0,
        total=64.06510177929309,
    ),
)

CONSERVATIVE_DEMAND_REWARD = RewardScenario(
    name="conservative_demand_reward",
    economy=CONSERVATIVE_DEMAND,
    population=INITIAL_POPULATION,
    productivity=INITIAL_PRODUCTIVITY,
    rounds_survived=1,
    expected=RewardExpectation(
        base_reward=13.073173633213308,
        productivity_bonus=0.0,
        survival_bonus=10.0,
        over_allocation_penalty=0.0,
        under_allocation_penalty=0.0,
        critical_penalty=0.0,
        total=23.073173633213308,
    ),
)

UNDERFUNDED_SURVIVABLE_REWARD = RewardScenario(
    name="underfunded_survivable_reward",
    economy=UNDERFUNDED_SURVIVABLE,
    population=INITIAL_POPULATION,
    productivity=INITIAL_PRODUCTIVITY,
    rounds_survived=1,
    expected=RewardExpectation(
        base_reward=12.909170656943036,
        productivity_bonus=0.0,
        survival_bonus=10.0,
        over_allocation_penalty=0.0,
        under_allocation_penalty=-10.0,
        critical_penalty=0.0,
        total=12.909170656943036,
    ),
)

CRITICAL_FAILURE_REWARD = RewardScenario(
    name="critical_failure_reward",
    economy=CRITICAL_FAILURE,
    population=INITIAL_POPULATION,
    productivity=INITIAL_PRODUCTIVITY,
    rounds_survived=1,
    expected=RewardExpectation(
        base_reward=6.907755778981887,
        productivity_bonus=0.0,
        survival_bonus=10.0,
        over_allocation_penalty=0.0,
        under_allocation_penalty=0.0,
        critical_penalty=-1000.0,
        total=-983.0922442210181,
    ),
)

WASTAGE_REWARD = RewardScenario(
    name="wastage_reward",
    economy=WASTAGE,
    population=INITIAL_POPULATION,
    productivity=INITIAL_PRODUCTIVITY,
    rounds_survived=1,
    expected=RewardExpectation(
        base_reward=13.251117798108481,
        productivity_bonus=0.0,
        survival_bonus=10.0,
        over_allocation_penalty=-5.0,
        under_allocation_penalty=0.0,
        critical_penalty=0.0,
        total=18.25111779810848,
    ),
)

REWARD_SCENARIOS: tuple[RewardScenario, ...] = (
    NORMAL_PROFIT_ZONE_REWARD,
    CONSERVATIVE_DEMAND_REWARD,
    UNDERFUNDED_SURVIVABLE_REWARD,
    CRITICAL_FAILURE_REWARD,
    WASTAGE_REWARD,
)
