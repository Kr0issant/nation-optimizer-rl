"""
revenue.py — Piecewise revenue-factor curve.

Pure functions, no state.  Matches spec 04 exactly.

Segments:
  1. x < critical           → None  (CRITICAL FAILURE)
  2. critical ≤ x < demand  → linear 0 → 1.0
  3. demand ≤ x ≤ surplus   → linear 1.0 → RF_MAX (1.8)
  4. x > surplus            → exponential decay from RF_MAX
"""

from __future__ import annotations

import math

from .config import CRITICAL_RATIO, RF_MAX, SURPLUS_RATIO, WASTAGE_RATIO


def revenue_factor(
    allocation: float,
    critical: float,
    demand: float,
    surplus: float,
    wastage: float,
    rf_max: float = RF_MAX,
) -> float | None:
    """
    Compute the revenue factor for a given allocation.

    Returns
    -------
    float
        Revenue factor in [0, rf_max] for viable allocations.
    None
        If allocation is below critical, triggering critical failure.
    """
    if allocation < critical:
        return None  # CRITICAL FAILURE — episode terminates

    if allocation < demand:
        # Segment A→B: linear from (critical, 0) to (demand, 1.0)
        return (allocation - critical) / (demand - critical)

    if allocation <= surplus:
        # Segment B→C: linear from (demand, 1.0) to (surplus, rf_max)
        t = (allocation - demand) / (surplus - demand)
        return 1.0 + (rf_max - 1.0) * t

    # Segment C→beyond: exponential decay from (surplus, rf_max)
    # k chosen so that RF(wastage) = 1.0
    k = math.log(rf_max) / (wastage - surplus)
    return rf_max * math.exp(-k * (allocation - surplus))


def calculate_revenue(
    allocation: float,
    critical: float,
    demand: float,
    surplus: float,
    wastage: float,
    productivity: float,
) -> float | None:
    """Calculate same-round revenue for a viable allocation."""
    factor = revenue_factor(allocation, critical, demand, surplus, wastage)
    if factor is None:
        return None
    return allocation * factor * productivity


def compute_thresholds(
    baseline: float,
    population: int,
    pop_0: int,
    event_multiplier: float = 1.0,
    *,
    critical_ratio: float = CRITICAL_RATIO,
    surplus_ratio: float = SURPLUS_RATIO,
    wastage_ratio: float = WASTAGE_RATIO,
) -> tuple[float, float, float, float]:
    """
    Compute the four key thresholds for a sector.

    Returns (critical, demand, surplus, wastage).
    """
    demand = baseline * (population / pop_0) * event_multiplier
    critical = demand * critical_ratio
    surplus = demand * surplus_ratio
    wastage = demand * wastage_ratio
    return critical, demand, surplus, wastage
