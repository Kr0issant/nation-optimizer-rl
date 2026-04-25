"""
reward.py — Per-step reward calculator.

Implements the full reward formula from spec 09:

  R_t = Base_Reward
      + Productivity_Bonus
      + Survival_Bonus
      + Over_Allocation_Penalty
      + Under_Allocation_Penalty
      - Critical_Penalty
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .sector import Sector


@dataclass
class RewardResult:
    """Breakdown of per-step reward components."""

    base_reward: float          # prosperity = total_revenue / population
    productivity_bonus: float   # +50 × (productivity - 1.0)
    survival_bonus: float       # +10 × round_num
    over_alloc_penalty: float   # -5 × count(sectors in wastage zone)
    under_alloc_penalty: float  # -10 × count(sectors between critical and demand)
    critical_penalty: float     # -1000 if any sector below critical

    @property
    def total(self) -> float:
        return (
            self.base_reward
            + self.productivity_bonus
            + self.survival_bonus
            + self.over_alloc_penalty
            + self.under_alloc_penalty
            + self.critical_penalty  # already negative
        )

    def to_dict(self) -> dict:
        return {
            "base_reward": round(self.base_reward, 6),
            "productivity_bonus": round(self.productivity_bonus, 4),
            "survival_bonus": round(self.survival_bonus, 4),
            "over_alloc_penalty": round(self.over_alloc_penalty, 4),
            "under_alloc_penalty": round(self.under_alloc_penalty, 4),
            "critical_penalty": round(self.critical_penalty, 4),
            "total": round(self.total, 6),
        }


def compute_reward(
    sectors: dict[str, "Sector"],
    total_revenue: float,
    population: int,
    productivity: float,
    round_num: int,
    critical_failed: bool,
    *,
    productivity_bonus_scale: float = 50.0,
    survival_bonus_per_round: float = 10.0,
    over_alloc_penalty_val: float = -5.0,
    under_alloc_penalty_val: float = -10.0,
    critical_penalty_val: float = -1000.0,
) -> RewardResult:
    """
    Compute the per-step reward.

    Parameters
    ----------
    sectors : dict[str, Sector]
        All sectors with computed allocation / thresholds.
    total_revenue : float
        Sum of department revenues this round.
    population : int
        Current population.
    productivity : float
        Current national productivity.
    round_num : int
        Current round number (1-indexed).
    critical_failed : bool
        True if any sector fell below critical this round.

    Returns
    -------
    RewardResult
        Full reward breakdown.
    """
    # Base reward = prosperity = revenue per capita
    base_reward = total_revenue / max(population, 1)

    # Productivity bonus
    prod_bonus = productivity_bonus_scale * (productivity - 1.0)

    # Survival bonus (accumulates over time)
    survival = survival_bonus_per_round * round_num

    # Zone penalties
    over_count = 0
    under_count = 0
    for s in sectors.values():
        if s.allocation > s.surplus:
            over_count += 1
        elif s.allocation < s.demand and s.allocation >= s.critical:
            under_count += 1

    over_penalty = over_alloc_penalty_val * over_count
    under_penalty = under_alloc_penalty_val * under_count

    # Critical penalty
    crit_penalty = critical_penalty_val if critical_failed else 0.0

    return RewardResult(
        base_reward=base_reward,
        productivity_bonus=prod_bonus,
        survival_bonus=survival,
        over_alloc_penalty=over_penalty,
        under_alloc_penalty=under_penalty,
        critical_penalty=crit_penalty,
    )
