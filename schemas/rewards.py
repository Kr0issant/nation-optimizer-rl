"""Reward breakdowns emitted by the environment."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RewardInfo:
    total: float
    base_reward: float = 0.0
    productivity_bonus: float = 0.0
    survival_bonus: float = 0.0
    allocation_penalty: float = 0.0
    critical_penalty: float = 0.0
