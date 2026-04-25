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


def revenue_factor(
    x: float,
    critical: float,
    demand: float,
    surplus: float,
    wastage: float,
    rf_max: float = 1.8,
) -> float | None:
    """
    Compute the revenue factor for a given allocation *x*.

    Returns
    -------
    float
        Revenue factor in [0, rf_max] for viable allocations.
    None
        If *x* < *critical* → CRITICAL FAILURE.
    """
    if x < critical:
        return None  # CRITICAL FAILURE — episode terminates

    if x < demand:
        # Segment A→B: linear from (critical, 0) to (demand, 1.0)
        return (x - critical) / (demand - critical)

    if x <= surplus:
        # Segment B→C: linear from (demand, 1.0) to (surplus, rf_max)
        t = (x - demand) / (surplus - demand)
        return 1.0 + (rf_max - 1.0) * t

    # Segment C→beyond: exponential decay from (surplus, rf_max)
    # k chosen so that RF(wastage) = 1.0
    k = math.log(rf_max) / (wastage - surplus)
    return rf_max * math.exp(-k * (x - surplus))


def compute_thresholds(
    baseline: float,
    population: int,
    pop_0: int,
    event_multiplier: float = 1.0,
    *,
    critical_ratio: float = 0.4,
    surplus_ratio: float = 1.5,
    wastage_ratio: float = 2.5,
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
