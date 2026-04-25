"""
productivity.py — Persistent national productivity tracker.

Productivity persists across rounds, creating long-term consequences.
  ΔProductivity = step × (avg_revenue_factor - 1.0)
  Productivity  = clamp(prev + Δ, min, max)
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import INITIAL_PRODUCTIVITY, MAX_PRODUCTIVITY, MIN_PRODUCTIVITY, PRODUCTIVITY_STEP


@dataclass
class ProductivityTracker:
    """Mutable productivity state, bounded to [min_val, max_val]."""

    value: float = INITIAL_PRODUCTIVITY
    min_val: float = MIN_PRODUCTIVITY
    max_val: float = MAX_PRODUCTIVITY
    step: float = PRODUCTIVITY_STEP

    def update(self, revenue_factors: float | list[float] | tuple[float, ...]) -> float:
        """
        Update productivity based on the average revenue factor of all sectors.

        Parameters
        ----------
        revenue_factors : float | Sequence[float]
            Revenue factors for all sectors, or a precomputed average.

        Returns
        -------
        float
            New productivity value after update.
        """
        if isinstance(revenue_factors, (list, tuple)):
            if not revenue_factors:
                avg_revenue_factor = 1.0
            else:
                avg_revenue_factor = sum(revenue_factors) / len(revenue_factors)
        else:
            avg_revenue_factor = revenue_factors

        delta = self.step * (avg_revenue_factor - 1.0)
        self.value = max(self.min_val, min(self.max_val, self.value + delta))
        return self.value
