"""
reward.py — Per-step reward calculator.

Implements the reward formula from spec 09 (Option A):

  R_t = Base_Reward
      + Productivity_Bonus
      + Survival_Bonus
      + Over_Allocation_Penalty
      + Under_Allocation_Penalty

The ``critical_penalty`` field on :class:`RewardBreakdown` is reserved for
episode-ending financial failure: :class:`core.game.NationGame` may set it to
``BANKRUPTCY_PENALTY`` when the treasury cannot cover mandatory critical funding.
There is no separate reward penalty for "critical failure" termination — that
outcome was removed under auto-funded critical (Option A).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .config import INITIAL_PRODUCTIVITY

if TYPE_CHECKING:
    from .sector import Sector


@dataclass
class RewardBreakdown:
    """Breakdown of per-step reward components."""

    base_reward: float          # prosperity = total_revenue / population
    productivity_bonus: float   # +50 × (productivity - 1.0)
    survival_bonus: float       # +10 × round_num
    over_alloc_penalty: float   # -5 × count(sectors in wastage zone)
    under_alloc_penalty: float  # -10 × count(sectors between critical and demand)
    critical_penalty: float     # set by NationGame on bankruptcy only (default 0)

    @property
    def over_allocation_penalty(self) -> float:
        """Descriptive alias for over-allocation penalty."""
        return self.over_alloc_penalty

    @property
    def under_allocation_penalty(self) -> float:
        """Descriptive alias for under-allocation penalty."""
        return self.under_alloc_penalty

    @property
    def total(self) -> float:
        return (
            self.base_reward
            + self.productivity_bonus
            + self.survival_bonus
            + self.over_alloc_penalty
            + self.under_alloc_penalty
            + self.critical_penalty  # bankruptcy override when set
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
    sectors: dict[str, "Sector"] | None = None,
    total_revenue: float | None = None,
    population: int | None = None,
    productivity: float = INITIAL_PRODUCTIVITY,
    round_num: int | None = None,
    *,
    prosperity: float | None = None,
    rounds_survived: int | None = None,
    over_allocated_count: int | None = None,
    under_allocated_count: int | None = None,
    productivity_bonus_scale: float = 50.0,
    survival_bonus_per_round: float = 10.0,
    over_alloc_penalty_val: float = -5.0,
    under_alloc_penalty_val: float = -10.0,
) -> RewardBreakdown:
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

    Returns
    -------
    RewardBreakdown
        Full reward breakdown.
    """
    if prosperity is None:
        if total_revenue is None or population is None:
            raise ValueError("provide prosperity or both total_revenue and population")
        prosperity = total_revenue / max(population, 1)
    base_reward = prosperity

    # Productivity bonus
    prod_bonus = productivity_bonus_scale * (productivity - 1.0)

    # Survival bonus (accumulates over time)
    if rounds_survived is None:
        rounds_survived = round_num or 0
    survival = survival_bonus_per_round * rounds_survived

    # Zone penalties
    over_count = over_allocated_count or 0
    under_count = under_allocated_count or 0
    if sectors is not None and (over_allocated_count is None or under_allocated_count is None):
        over_count = 0
        under_count = 0
        for sector in sectors.values():
            if sector.allocation > sector.surplus:
                over_count += 1
            elif sector.allocation < sector.demand and sector.allocation >= sector.critical:
                under_count += 1

    over_penalty = over_alloc_penalty_val * over_count
    under_penalty = under_alloc_penalty_val * under_count

    return RewardBreakdown(
        base_reward=base_reward,
        productivity_bonus=prod_bonus,
        survival_bonus=survival,
        over_alloc_penalty=over_penalty,
        under_alloc_penalty=under_penalty,
        critical_penalty=0.0,
    )


RewardResult = RewardBreakdown
