"""
sector.py — Individual sector / department state.

Each Sector holds its baseline plus transient per-round state
(demand, thresholds, allocation, revenue factor, revenue, consumption).
The game orchestrator resets per-round fields each step.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import (
    CRITICAL_RATIO,
    INITIAL_POPULATION,
    INITIAL_PRODUCTIVITY,
    RF_MAX,
    SURPLUS_RATIO,
    WASTAGE_RATIO,
)
from .revenue import compute_thresholds, revenue_factor


class _ThresholdAccessor:
    """Callable numeric threshold for compatibility with stored attributes."""

    def __init__(self, sector: "Sector", threshold_name: str) -> None:
        self._sector = sector
        self._threshold_name = threshold_name
        self._value = 0.0

    def set(self, value: float) -> None:
        self._value = value

    def __call__(self, population: int) -> float:
        critical, demand, surplus, wastage = self._sector.thresholds(population)
        return {
            "critical": critical,
            "demand": demand,
            "surplus": surplus,
            "wastage": wastage,
        }[self._threshold_name]

    def __float__(self) -> float:
        return self._value

    def __round__(self, ndigits: int | None = None) -> float:
        return round(self._value, ndigits) if ndigits is not None else round(self._value)

    def __repr__(self) -> str:
        return repr(self._value)

    def __eq__(self, other: object) -> bool:
        try:
            return self._value == float(other)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return False

    def __lt__(self, other: Any) -> bool:
        return self._value < float(other)

    def __le__(self, other: Any) -> bool:
        return self._value <= float(other)

    def __gt__(self, other: Any) -> bool:
        return self._value > float(other)

    def __ge__(self, other: Any) -> bool:
        return self._value >= float(other)

    def __add__(self, other: Any) -> float:
        return self._value + float(other)

    def __radd__(self, other: Any) -> float:
        return float(other) + self._value

    def __sub__(self, other: Any) -> float:
        return self._value - float(other)

    def __rsub__(self, other: Any) -> float:
        return float(other) - self._value

    def __mul__(self, other: Any) -> float:
        return self._value * float(other)

    def __rmul__(self, other: Any) -> float:
        return float(other) * self._value

    def __truediv__(self, other: Any) -> float:
        return self._value / float(other)

    def __rtruediv__(self, other: Any) -> float:
        return float(other) / self._value


@dataclass
class Sector:
    """Mutable state for one government department."""

    # ── Identity (set once at episode start) ────────────────────
    name: str
    baseline: float
    full_name: str = ""
    description: str = ""

    # ── Per-round computed state ────────────────────────────────
    event_multiplier: float = 1.0

    demand: _ThresholdAccessor = field(init=False)
    critical: _ThresholdAccessor = field(init=False)
    surplus: _ThresholdAccessor = field(init=False)
    wastage: _ThresholdAccessor = field(init=False)

    allocation: float = 0.0
    revenue_factor_value: float = 0.0
    revenue: float = 0.0
    consumption: float = 0.0

    # ── Config ratios (injected from GameConfig) ────────────────
    _critical_ratio: float = field(default=CRITICAL_RATIO, repr=False)
    _surplus_ratio: float = field(default=SURPLUS_RATIO, repr=False)
    _wastage_ratio: float = field(default=WASTAGE_RATIO, repr=False)
    _rf_max: float = field(default=RF_MAX, repr=False)

    def __post_init__(self) -> None:
        self.demand = _ThresholdAccessor(self, "demand")
        self.critical = _ThresholdAccessor(self, "critical")
        self.surplus = _ThresholdAccessor(self, "surplus")
        self.wastage = _ThresholdAccessor(self, "wastage")
        self.update_thresholds(INITIAL_POPULATION, INITIAL_POPULATION)

    # ── Lifecycle ───────────────────────────────────────────────

    def reset_round(self) -> None:
        """Clear transient state before a new round."""
        self.event_multiplier = 1.0
        self.allocation = 0.0
        self.revenue_factor_value = 0.0
        self.revenue = 0.0
        self.consumption = 0.0

    def update_thresholds(self, population: int, pop_0: int) -> None:
        """Recalculate demand/critical/surplus/wastage for this round."""
        critical, demand, surplus, wastage = compute_thresholds(
            baseline=self.baseline,
            population=population,
            pop_0=pop_0,
            event_multiplier=self.event_multiplier,
            critical_ratio=self._critical_ratio,
            surplus_ratio=self._surplus_ratio,
            wastage_ratio=self._wastage_ratio,
        )
        self.critical.set(critical)
        self.demand.set(demand)
        self.surplus.set(surplus)
        self.wastage.set(wastage)

    def thresholds(self, population: int) -> tuple[float, float, float, float]:
        """Return (critical, demand, surplus, wastage) for a population."""
        return compute_thresholds(
            baseline=self.baseline,
            population=population,
            pop_0=INITIAL_POPULATION,
            event_multiplier=self.event_multiplier,
            critical_ratio=self._critical_ratio,
            surplus_ratio=self._surplus_ratio,
            wastage_ratio=self._wastage_ratio,
        )

    def allocate(self, amount: float) -> None:
        """Store the current round allocation."""
        self.allocation = amount

    def compute_revenue(
        self,
        population: int | None = None,
        productivity: float = INITIAL_PRODUCTIVITY,
        *,
        allocation: float | None = None,
    ) -> float | None:
        """
        Compute revenue using the current or provided allocation.

        Returns
        -------
        float
            Revenue generated by this sector.
        None
            If allocation is below the critical threshold (episode must end).
        """
        if allocation is not None:
            self.allocate(allocation)
        if population is not None:
            self.update_thresholds(population=population, pop_0=INITIAL_POPULATION)

        rf = revenue_factor(
            allocation=self.allocation,
            critical=float(self.critical),
            demand=float(self.demand),
            surplus=float(self.surplus),
            wastage=float(self.wastage),
            rf_max=self._rf_max,
        )

        if rf is None:
            self.revenue_factor_value = 0.0
            self.revenue = 0.0
            return None  # CRITICAL FAILURE

        self.revenue_factor_value = rf
        self.revenue = self.allocation * rf * productivity
        return self.revenue

    def is_critical_failure(self, population: int) -> bool:
        """Return true when allocation is below the critical threshold."""
        return self.allocation < self.critical(population)

    def compute_consumption(self) -> float:
        """
        Consumption = min(allocation, demand).
        Surplus (allocation - consumption) will be returned to treasury.

        Returns the surplus amount.
        """
        self.consumption = min(self.allocation, float(self.demand))
        return self.allocation - self.consumption  # surplus

    # ── Serialisation helpers ───────────────────────────────────

    def to_dict(self) -> dict:
        """Snapshot of sector state for observations / logging."""
        return {
            "name": self.name,
            "full_name": self.full_name,
            "baseline": self.baseline,
            "demand": round(self.demand, 4),
            "critical": round(self.critical, 4),
            "surplus": round(self.surplus, 4),
            "wastage": round(self.wastage, 4),
            "allocation": round(self.allocation, 4),
            "revenue_factor": round(self.revenue_factor_value, 6),
            "revenue": round(self.revenue, 4),
            "consumption": round(self.consumption, 4),
            "event_multiplier": round(self.event_multiplier, 4),
        }

    @classmethod
    def from_config(cls, name: str, info: dict, config) -> "Sector":
        """Build a Sector from sectors.json data + a GameConfig."""
        return cls(
            name=name,
            baseline=info["baseline"] if isinstance(info, dict) else info,
            full_name=(info.get("full_name", name) if isinstance(info, dict) else name),
            description=(info.get("description", "") if isinstance(info, dict) else ""),
            _critical_ratio=config.CRITICAL_RATIO,
            _surplus_ratio=config.SURPLUS_RATIO,
            _wastage_ratio=config.WASTAGE_RATIO,
            _rf_max=config.RF_MAX,
        )
