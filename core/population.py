"""
population.py — Population dynamics.

  birth_rate  = base_birth × productivity
  death_rate  = base_death + crisis_penalty
  population  = round(prev × (1 + birth_rate - death_rate))
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PopulationTracker:
    """Mutable population state."""

    value: int = 1_000_000
    birth_rate_base: float = 0.005
    death_rate_base: float = 0.002
    crisis_death_penalty: float = 0.01

    def update(self, productivity: float, crisis_occurred: bool) -> int:
        """
        Update population for the current round.

        Parameters
        ----------
        productivity : float
            Current national productivity level.
        crisis_occurred : bool
            True if a critical-severity event occurred this round.

        Returns
        -------
        int
            New population (always ≥ 1 to avoid division by zero).
        """
        birth_rate = self.birth_rate_base * productivity
        death_rate = self.death_rate_base + (
            self.crisis_death_penalty if crisis_occurred else 0.0
        )
        self.value = max(1, round(self.value * (1 + birth_rate - death_rate)))
        return self.value
