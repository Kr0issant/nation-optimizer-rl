"""
config.py — All game constants and tunable parameters.

Single source of truth. Reads sector definitions from sectors.json.
Frozen dataclass: safe to share across modules, cannot be mutated.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar


INITIAL_TREASURY = 1000
BASELINE_TAX = 100
INITIAL_POPULATION = 1_000_000
INITIAL_PRODUCTIVITY = 1.0
MIN_PRODUCTIVITY = 0.5
MAX_PRODUCTIVITY = 2.0
MAX_ROUNDS = 50
CRITICAL_RATIO = 0.4
SURPLUS_RATIO = 1.5
WASTAGE_RATIO = 2.5
RF_MAX = 1.8
PRODUCTIVITY_STEP = 0.05
BASE_BIRTH_RATE = 0.005
BASE_DEATH_RATE = 0.002
CRISIS_DEATH_PENALTY = 0.01


@dataclass(frozen=True)
class GameConfig:
    """Immutable configuration for a NationGame episode."""

    # ── Population ──────────────────────────────────────────────
    POP_0: int = INITIAL_POPULATION

    # ── Treasury ────────────────────────────────────────────────
    INITIAL_TREASURY: float = float(INITIAL_TREASURY)
    BASELINE_TAX: float = float(BASELINE_TAX)

    # ── Productivity ────────────────────────────────────────────
    INITIAL_PRODUCTIVITY: float = INITIAL_PRODUCTIVITY
    PRODUCTIVITY_MIN: float = MIN_PRODUCTIVITY
    PRODUCTIVITY_MAX: float = MAX_PRODUCTIVITY
    PRODUCTIVITY_STEP: float = PRODUCTIVITY_STEP

    # ── Revenue-curve ratios (relative to Demand) ───────────────
    CRITICAL_RATIO: float = CRITICAL_RATIO
    SURPLUS_RATIO: float = SURPLUS_RATIO
    WASTAGE_RATIO: float = WASTAGE_RATIO
    RF_MAX: float = RF_MAX  # peak revenue factor at surplus

    # ── Population dynamics ─────────────────────────────────────
    BIRTH_RATE_BASE: float = BASE_BIRTH_RATE
    DEATH_RATE_BASE: float = BASE_DEATH_RATE
    CRISIS_DEATH_PENALTY: float = CRISIS_DEATH_PENALTY

    # ── Episode limits ──────────────────────────────────────────
    MAX_ROUNDS: int = MAX_ROUNDS
    SHUTDOWN_THRESHOLD: int = 2  # consecutive zero-alloc rounds

    # ── Reward components ───────────────────────────────────────
    PRODUCTIVITY_BONUS_SCALE: float = 50.0
    SURVIVAL_BONUS_PER_ROUND: float = 10.0
    OVER_ALLOC_PENALTY: float = -5.0
    UNDER_ALLOC_PENALTY: float = -10.0
    CRITICAL_PENALTY: float = -1000.0
    BANKRUPTCY_PENALTY: float = -1000.0

    # ── Prosperity threshold (early-success termination) ────────
    PROSPERITY_THRESHOLD: float | None = None  # None = disabled
    PROSPERITY_STREAK: int = 5  # consecutive rounds above threshold

    # ── Sector data (populated from JSON) ───────────────────────
    SECTOR_BASELINES: dict[str, int] = field(default_factory=dict)
    SECTOR_ORDER: tuple[str, ...] = ()
    SECTOR_META: dict[str, dict] = field(default_factory=dict)

    # ── Class-level path to default JSON ────────────────────────
    _DEFAULT_JSON: ClassVar[Path] = Path(__file__).parent / "sectors.json"

    # ── Factory ─────────────────────────────────────────────────
    @classmethod
    def from_json(cls, path: str | Path | None = None, **overrides) -> "GameConfig":
        """
        Build a GameConfig from sectors.json.

        Any keyword argument overrides the corresponding field.
        """
        path = Path(path) if path else cls._DEFAULT_JSON
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sectors_raw: dict = data.get("sectors", {})
        baselines = {name: info["baseline"] for name, info in sectors_raw.items()}
        order = tuple(sectors_raw.keys())
        meta = {
            name: {
                "full_name": info.get("full_name", name),
                "description": info.get("description", ""),
            }
            for name, info in sectors_raw.items()
        }

        # Merge JSON-level scalars with dataclass defaults
        json_fields = {
            "POP_0": data.get("initial_population"),
            "INITIAL_TREASURY": data.get("initial_treasury"),
            "BASELINE_TAX": data.get("baseline_tax"),
            "INITIAL_PRODUCTIVITY": data.get("initial_productivity"),
            "PRODUCTIVITY_MIN": (data.get("productivity_bounds") or [None])[0],
            "PRODUCTIVITY_MAX": (data.get("productivity_bounds") or [None, None])[1],
            "PRODUCTIVITY_STEP": data.get("productivity_step"),
            "MAX_ROUNDS": data.get("max_rounds"),
            "CRITICAL_RATIO": data.get("critical_ratio"),
            "SURPLUS_RATIO": data.get("surplus_ratio"),
            "WASTAGE_RATIO": data.get("wastage_ratio"),
            "RF_MAX": data.get("rf_max"),
            "BIRTH_RATE_BASE": data.get("birth_rate_base"),
            "DEATH_RATE_BASE": data.get("death_rate_base"),
            "CRISIS_DEATH_PENALTY": data.get("crisis_death_penalty"),
        }
        # Drop None values so dataclass defaults apply
        json_fields = {k: v for k, v in json_fields.items() if v is not None}

        return cls(
            **json_fields,
            SECTOR_BASELINES=baselines,
            SECTOR_ORDER=order,
            SECTOR_META=meta,
            **overrides,
        )


# ── Module-level convenience instance ──────────────────────────
DEFAULT_CONFIG = GameConfig.from_json()
