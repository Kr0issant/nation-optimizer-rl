"""
events.py — Stochastic event engine.

Loads events.json, generates events per round based on the probability
distribution, and applies event multipliers to sectors + treasury injections.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .sector import Sector
    from .treasury import Treasury


# ── Event data object ───────────────────────────────────────────

@dataclass
class Event:
    """An event instance generated for a specific round."""

    id: str
    name: str
    severity: int
    affected_sectors: dict[str, float]  # sector_name → multiplier
    category: str
    narrative: str
    description: str = ""
    _treasury_injection: float = field(default=0.0, repr=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "severity": self.severity,
            "affected_sectors": dict(self.affected_sectors),
            "description": self.description,
            "narrative": self.narrative,
            "category": self.category,
        }


# ── Event catalog & engine ──────────────────────────────────────

class EventEngine:
    """
    Loads the event catalog from JSON and generates / applies events
    each game round.
    """

    _DEFAULT_JSON: Path = Path(__file__).parent / "events.json"

    def __init__(
        self,
        rng: random.Random | None = None,
        events_path: str | Path | None = None,
    ):
        path = Path(events_path) if events_path else self._DEFAULT_JSON
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.rng = rng or random.Random()

        # Event distribution weights
        self._distribution: dict[str, float] = data["event_distribution"]

        # Catalogs
        self._negative: list[dict] = data.get("negative_events", [])
        self._positive: list[dict] = data.get("positive_events", [])
        self._black_swan: list[dict] = data.get("black_swan_events", [])
        self.catalog: list[dict] = [*self._negative, *self._positive, *self._black_swan]

        # Pre-index by category for fast lookup
        self._by_category: dict[str, list[dict]] = {
            "minor": [e for e in self._negative if e.get("category") == "minor"]
                   + self._positive,  # positive events are always minor
            "moderate": [e for e in self._negative if e.get("category") == "moderate"],
            "critical": [e for e in self._negative if e.get("category") == "critical"]
                      + self._black_swan,
            "compound": self._black_swan,
        }

    # ── Public API ──────────────────────────────────────────────

    def generate_events(
        self,
        rng: random.Random | list[str] | None = None,
        sector_names: list[str] | None = None,
    ) -> list[Event]:
        """
        Generate 0–2 events for the current round.

        Parameters
        ----------
        sector_names : list[str] | None
            Available sector names (needed for black-swan random targeting).

        Returns
        -------
        list[Event]
            Generated events (may be empty for a quiet round).
        """
        if isinstance(rng, random.Random):
            active_rng = rng
        else:
            active_rng = self.rng
            if isinstance(rng, list) and sector_names is None:
                sector_names = rng

        tier = self._roll_tier(active_rng)

        if tier == "no_event":
            return []

        if tier == "compound":
            # Compound crisis: 2 black swan events simultaneously
            return self._generate_compound(sector_names or [], active_rng)

        # Single event from the appropriate category pool
        pool = self._by_category.get(tier, [])
        if not pool:
            return []

        template = active_rng.choice(pool)
        return [self._instantiate(template, sector_names, active_rng, category=tier)]

    def apply_events(
        self,
        events: list[Event],
        sectors: dict[str, "Sector"],
        treasury: "Treasury",
    ) -> bool:
        """
        Apply event effects to sectors and treasury.

        - Negative events: multiply affected sectors' event_multiplier
        - Positive events: multiply (reduce) demand AND inject treasury cash
        - Black swan events: extreme multipliers

        Returns True if any event had severity ≥ 4 (treated as crisis
        for population death-rate penalty).
        """
        crisis = False

        for event in events:
            # Apply sector demand multipliers (multiplicative stacking)
            for sector_name, multiplier in event.affected_sectors.items():
                if sector_name in sectors:
                    sectors[sector_name].event_multiplier *= multiplier

            # Treasury injection (positive events only)
            if event._treasury_injection > 0:
                treasury.credit(event._treasury_injection)

            if event.severity >= 4:
                crisis = True

        return crisis

    # ── Internal helpers ────────────────────────────────────────

    def _roll_tier(self, rng: random.Random) -> str:
        """Weighted random draw from the event distribution."""
        tiers = list(self._distribution.keys())
        weights = list(self._distribution.values())
        return rng.choices(tiers, weights=weights, k=1)[0]

    def _instantiate(
        self,
        template: dict,
        sector_names: list[str] | None = None,
        rng: random.Random | None = None,
        category: str | None = None,
    ) -> Event:
        """Turn a catalog template into a concrete Event instance."""
        rng = rng or self.rng
        # Black swan events have fixed severity
        if "severity" in template and not isinstance(template["severity"], list):
            severity = template["severity"]
        else:
            lo, hi = template.get("severity_range", [1, 5])
            severity = rng.randint(lo, hi)

        # Determine affected sectors and multipliers
        if "affected_sectors" in template:
            affected = dict(template["affected_sectors"])
        elif "primary_multiplier" in template:
            # Black swan — pick a random primary sector
            primary = rng.choice(sector_names) if sector_names else "Social"
            affected = {primary: template["primary_multiplier"]}
            secondary_mult = template.get("secondary_multiplier", 1.5)
            for name in (sector_names or []):
                if name != primary:
                    affected[name] = secondary_mult
        elif "affected_sectors_multiplier_range" in template:
            # Compound crisis — all sectors hit hard
            lo, hi = template["affected_sectors_multiplier_range"]
            affected = {
                name: round(rng.uniform(lo, hi), 2)
                for name in (sector_names or [])
            }
        else:
            affected = {}

        # Pick narrative
        narratives = template.get("narratives", [template.get("description", "")])
        narrative = rng.choice(narratives) if narratives else ""

        cat = category or template.get("category", "minor")

        return Event(
            id=template.get("id", "unknown"),
            name=template.get("name", "Unknown Event"),
            severity=severity,
            affected_sectors=affected,
            category=cat,
            narrative=narrative,
            description=template.get("description", ""),
            _treasury_injection=float(template.get("treasury_injection", 0)),
        )

    def _generate_compound(self, sector_names: list[str], rng: random.Random) -> list[Event]:
        """Generate 2 black-swan events for a compound crisis."""
        events: list[Event] = []
        for template in rng.sample(
            self._black_swan, k=min(2, len(self._black_swan))
        ):
            events.append(self._instantiate(template, sector_names, rng, category="compound"))
        return events


def generate_events(rng: random.Random) -> list[Event]:
    """Generate catalog events using a caller-provided RNG."""
    return EventEngine().generate_events(rng)


def sector_multipliers(events: list[Event]) -> dict[str, float]:
    """Aggregate sector demand multipliers multiplicatively."""
    multipliers: dict[str, float] = {}
    for event in events:
        for sector_name, multiplier in event.affected_sectors.items():
            multipliers[sector_name] = multipliers.get(sector_name, 1.0) * multiplier
    return multipliers
