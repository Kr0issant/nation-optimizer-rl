"""Helpers for Phase 3 discretionary (above-critical) budget amounts."""

from __future__ import annotations

from schemas.observations import Observation


def discretionary_pool(observation: Observation) -> float:
    """Treasury left after the nation reserves critical minimums for all sectors."""
    tc = float(getattr(observation, "total_critical", 0.0) or 0.0)
    return max(0.0, float(observation.treasury) - tc)


def discretionary_for_target_total(
    *,
    want_total: float,
    own_critical: float,
    pool: float,
) -> float:
    """Map a desired *total* allocation to a valid discretionary request."""
    d = max(0.0, want_total - own_critical)
    return min(d, max(0.0, pool))
