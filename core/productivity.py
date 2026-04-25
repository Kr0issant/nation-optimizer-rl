"""
productivity.py — Persistent national productivity tracker.

Productivity persists across rounds, creating long-term consequences.
  ΔProductivity = step × (avg_revenue_factor - 1.0)
  Productivity  = clamp(prev + Δ, min, max)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProductivityTracker:
    """Mutable productivity state, bounded to [min_val, max_val]."""

    value: float = 1.0
    min_val: float = 0.5
    max_val: float = 2.0
    step: float = 0.05

    def update(self, avg_revenue_factor: float) -> float:
        """
        Update productivity based on the average revenue factor of all sectors.

        Parameters
        ----------
        avg_revenue_factor : float
            Mean RF across all departments this round.

        Returns
        -------
        float
            New productivity value after update.
        """
        delta = self.step * (avg_revenue_factor - 1.0)
        self.value = max(self.min_val, min(self.max_val, self.value + delta))
        return self.value
