"""
game.py — Main game orchestrator.

NationGame is the pure-Python game engine.  It has zero framework
dependencies and communicates entirely via plain dicts / dataclasses.

Input:  allocations dict  {"Social": 90, "Defense": 150, …}
Output: StepResult with treasury, revenues, reward, done, etc.

The server/ layer (OpenEnv wrapper) sits on top of this.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from .config import DEFAULT_CONFIG, GameConfig
from .events import Event, EventEngine
from .population import PopulationTracker
from .productivity import ProductivityTracker
from .reward import RewardResult, compute_reward
from .sector import Sector
from .treasury import Treasury


# ── Step result ─────────────────────────────────────────────────

@dataclass
class StepResult:
    """Everything the environment needs after one round."""

    # Round info
    round_num: int
    year: int
    quarter: int

    # Treasury
    treasury: float

    # Per-sector data
    allocations: dict[str, float]
    revenue_factors: dict[str, float]
    revenues: dict[str, float]
    consumptions: dict[str, float]
    demands: dict[str, float]

    # Aggregates
    total_revenue: float
    total_allocation: float
    surplus_returned: float

    # Persistent state
    population: int
    productivity: float

    # Reward
    reward: RewardResult

    # Events
    events: list[Event]
    crisis_occurred: bool

    # Termination
    done: bool
    termination_reason: str | None  # CRITICAL_FAILURE | BANKRUPTCY | SHUTDOWN | MAX_ROUNDS | PROSPERITY_ACHIEVED

    def to_dict(self) -> dict:
        """Serialise for agent observation / logging."""
        return {
            "round_num": self.round_num,
            "year": self.year,
            "quarter": self.quarter,
            "treasury": round(self.treasury, 4),
            "allocations": {k: round(v, 4) for k, v in self.allocations.items()},
            "revenue_factors": {k: round(v, 6) for k, v in self.revenue_factors.items()},
            "revenues": {k: round(v, 4) for k, v in self.revenues.items()},
            "consumptions": {k: round(v, 4) for k, v in self.consumptions.items()},
            "demands": {k: round(v, 4) for k, v in self.demands.items()},
            "total_revenue": round(self.total_revenue, 4),
            "total_allocation": round(self.total_allocation, 4),
            "surplus_returned": round(self.surplus_returned, 4),
            "population": self.population,
            "productivity": round(self.productivity, 6),
            "reward": self.reward.to_dict(),
            "events": [e.to_dict() for e in self.events],
            "crisis_occurred": self.crisis_occurred,
            "done": self.done,
            "termination_reason": self.termination_reason,
        }


# ── Main game class ────────────────────────────────────────────

class NationGame:
    """
    Pure-Python game engine for the Nation Simulator.

    Usage::

        game = NationGame(seed=42)
        obs = game.reset()

        while not obs["done"]:
            allocations = my_agent.decide(obs)
            result = game.step(allocations)
            obs = result.to_dict()
    """

    def __init__(
        self,
        config: GameConfig | None = None,
        seed: int | None = None,
    ):
        self.config = config or DEFAULT_CONFIG
        self.rng = random.Random(seed)

        # These are initialised in reset()
        self._sectors: dict[str, Sector] = {}
        self._treasury: Treasury | None = None
        self._productivity: ProductivityTracker | None = None
        self._population: PopulationTracker | None = None
        self._event_engine: EventEngine | None = None

        self._round: int = 0
        self._done: bool = True
        self._termination_reason: str | None = None
        self._shutdown_counter: int = 0
        self._prosperity_streak: int = 0
        self._event_ledger: list[Event] = []

    # ── Reset ───────────────────────────────────────────────────

    def reset(self) -> dict:
        """
        Reset the game to the initial state.

        Returns
        -------
        dict
            Initial observation (treasury, sectors, population, etc.).
        """
        cfg = self.config

        # Sectors
        self._sectors = {}
        for name in cfg.SECTOR_ORDER:
            meta = cfg.SECTOR_META.get(name, {})
            info = {"baseline": cfg.SECTOR_BASELINES[name], **meta}
            self._sectors[name] = Sector.from_config(name, info, cfg)

        # Treasury
        self._treasury = Treasury(
            balance=cfg.INITIAL_TREASURY,
            baseline_tax=cfg.BASELINE_TAX,
        )

        # Trackers
        self._productivity = ProductivityTracker(
            value=cfg.INITIAL_PRODUCTIVITY,
            min_val=cfg.PRODUCTIVITY_MIN,
            max_val=cfg.PRODUCTIVITY_MAX,
            step=cfg.PRODUCTIVITY_STEP,
        )
        self._population = PopulationTracker(
            value=cfg.POP_0,
            birth_rate_base=cfg.BIRTH_RATE_BASE,
            death_rate_base=cfg.DEATH_RATE_BASE,
            crisis_death_penalty=cfg.CRISIS_DEATH_PENALTY,
        )

        # Event engine
        self._event_engine = EventEngine(rng=self.rng)

        # Episode state
        self._round = 0
        self._done = False
        self._termination_reason = None
        self._shutdown_counter = 0
        self._prosperity_streak = 0
        self._event_ledger = []

        return self._build_observation(events=[], crisis=False)

    # ── Step ────────────────────────────────────────────────────

    def step(self, allocations: dict[str, float]) -> StepResult:
        """
        Execute one complete round (Phases 1-9).

        Parameters
        ----------
        allocations : dict[str, float]
            Budget allocation per sector, e.g. ``{"Social": 90, "Defense": 150}``.
            Missing sectors receive 0.  Values must be ≥ 0.

        Returns
        -------
        StepResult
            Full round data including reward, termination, etc.
        """
        if self._done:
            raise RuntimeError("Game is over. Call reset() to start a new episode.")

        cfg = self.config
        self._round += 1

        # ── Phase 1: Event revelation ───────────────────────────
        for s in self._sectors.values():
            s.reset_round()

        events = self._event_engine.generate_events(
            sector_names=list(self._sectors.keys()),
        )

        # ── Apply event multipliers to sectors + treasury inject
        crisis = self._event_engine.apply_events(
            events, self._sectors, self._treasury,
        )
        self._event_ledger.extend(events)

        # ── Update thresholds (with population + event mults) ──
        for s in self._sectors.values():
            s.update_thresholds(
                population=self._population.value,
                pop_0=cfg.POP_0,
            )

        # ── Normalise allocations dict ──────────────────────────
        alloc = {
            name: max(0.0, float(allocations.get(name, 0.0)))
            for name in self._sectors
        }
        total_allocation = sum(alloc.values())

        # ── Phase 5a: Critical threshold check ──────────────────
        critical_failed = False
        for name, sector in self._sectors.items():
            sector.allocation = alloc[name]
            if alloc[name] < sector.critical:
                critical_failed = True

        if critical_failed:
            return self._terminate(
                alloc, events, crisis,
                reason="CRITICAL_FAILURE",
                critical_failed=True,
            )

        # ── Phase 5b: Debit treasury ────────────────────────────
        self._treasury.debit(total_allocation)

        # ── Phase 6: Consumption ────────────────────────────────
        total_surplus = 0.0
        for s in self._sectors.values():
            total_surplus += s.compute_consumption()

        # ── Phase 7: Revenue calculation ────────────────────────
        total_revenue = 0.0
        for name, sector in self._sectors.items():
            rev = sector.compute_revenue(
                allocation=alloc[name],
                productivity=self._productivity.value,
            )
            # rev should never be None here (critical check passed)
            total_revenue += rev or 0.0

        # Credit revenue to treasury
        self._treasury.credit(total_revenue)

        # ── Phase 8: Surplus return ─────────────────────────────
        self._treasury.credit(total_surplus)

        # ── Baseline tax ────────────────────────────────────────
        self._treasury.apply_baseline_tax()

        # ── Phase 9: State updates & termination ────────────────

        # Productivity update
        rf_values = [s.revenue_factor_value for s in self._sectors.values()]
        avg_rf = sum(rf_values) / len(rf_values) if rf_values else 1.0
        self._productivity.update(avg_rf)

        # Population update
        self._population.update(self._productivity.value, crisis)

        # Shutdown counter
        if total_allocation == 0:
            self._shutdown_counter += 1
        else:
            self._shutdown_counter = 0

        # Treasury snapshot
        self._treasury.snapshot()

        # ── Check termination conditions ────────────────────────
        done = False
        reason = None

        if self._shutdown_counter >= cfg.SHUTDOWN_THRESHOLD:
            done, reason = True, "SHUTDOWN"
        elif self._treasury.is_bankrupt():
            done, reason = True, "BANKRUPTCY"
        elif self._round >= cfg.MAX_ROUNDS:
            done, reason = True, "MAX_ROUNDS"
        elif cfg.PROSPERITY_THRESHOLD is not None:
            prosperity = total_revenue / max(self._population.value, 1)
            if prosperity >= cfg.PROSPERITY_THRESHOLD:
                self._prosperity_streak += 1
                if self._prosperity_streak >= cfg.PROSPERITY_STREAK:
                    done, reason = True, "PROSPERITY_ACHIEVED"
            else:
                self._prosperity_streak = 0

        self._done = done
        self._termination_reason = reason

        # ── Compute reward ──────────────────────────────────────
        reward = compute_reward(
            sectors=self._sectors,
            total_revenue=total_revenue,
            population=self._population.value,
            productivity=self._productivity.value,
            round_num=self._round,
            critical_failed=False,
            productivity_bonus_scale=cfg.PRODUCTIVITY_BONUS_SCALE,
            survival_bonus_per_round=cfg.SURVIVAL_BONUS_PER_ROUND,
            over_alloc_penalty_val=cfg.OVER_ALLOC_PENALTY,
            under_alloc_penalty_val=cfg.UNDER_ALLOC_PENALTY,
            critical_penalty_val=cfg.CRITICAL_PENALTY,
        )

        # Add bankruptcy penalty on top if applicable
        if reason == "BANKRUPTCY":
            reward = RewardResult(
                base_reward=reward.base_reward,
                productivity_bonus=reward.productivity_bonus,
                survival_bonus=reward.survival_bonus,
                over_alloc_penalty=reward.over_alloc_penalty,
                under_alloc_penalty=reward.under_alloc_penalty,
                critical_penalty=cfg.BANKRUPTCY_PENALTY,
            )

        year, quarter = self._time_display()

        return StepResult(
            round_num=self._round,
            year=year,
            quarter=quarter,
            treasury=self._treasury.balance,
            allocations={n: s.allocation for n, s in self._sectors.items()},
            revenue_factors={n: s.revenue_factor_value for n, s in self._sectors.items()},
            revenues={n: s.revenue for n, s in self._sectors.items()},
            consumptions={n: s.consumption for n, s in self._sectors.items()},
            demands={n: s.demand for n, s in self._sectors.items()},
            total_revenue=total_revenue,
            total_allocation=total_allocation,
            surplus_returned=total_surplus,
            population=self._population.value,
            productivity=self._productivity.value,
            reward=reward,
            events=events,
            crisis_occurred=crisis,
            done=done,
            termination_reason=reason,
        )

    # ── Properties ──────────────────────────────────────────────

    @property
    def current_round(self) -> int:
        return self._round

    @property
    def is_done(self) -> bool:
        return self._done

    @property
    def sector_names(self) -> list[str]:
        return list(self._sectors.keys())

    @property
    def event_ledger(self) -> list[Event]:
        return list(self._event_ledger)

    @property
    def state(self) -> dict:
        """Full game state for serialisation / checkpointing."""
        return {
            "round": self._round,
            "done": self._done,
            "termination_reason": self._termination_reason,
            "treasury": self._treasury.balance if self._treasury else 0,
            "population": self._population.value if self._population else 0,
            "productivity": self._productivity.value if self._productivity else 0,
            "sectors": {
                n: s.to_dict() for n, s in self._sectors.items()
            },
            "event_ledger": [e.to_dict() for e in self._event_ledger],
            "shutdown_counter": self._shutdown_counter,
            "prosperity_streak": self._prosperity_streak,
        }

    # ── Internal helpers ────────────────────────────────────────

    def _terminate(
        self,
        alloc: dict[str, float],
        events: list[Event],
        crisis: bool,
        reason: str,
        critical_failed: bool,
    ) -> StepResult:
        """Build a StepResult for an immediately-terminating round."""
        cfg = self.config
        self._done = True
        self._termination_reason = reason

        total_alloc = sum(alloc.values())

        # On critical failure no revenue is generated (spec 04)
        total_revenue = 0.0

        # Prosperity at termination = (Treasury + Revenue) / Population
        # Revenue is 0 on critical failure
        reward = compute_reward(
            sectors=self._sectors,
            total_revenue=total_revenue,
            population=self._population.value,
            productivity=self._productivity.value,
            round_num=self._round,
            critical_failed=critical_failed,
            over_allocated_count=0,
            under_allocated_count=0,
            productivity_bonus_scale=cfg.PRODUCTIVITY_BONUS_SCALE,
            survival_bonus_per_round=cfg.SURVIVAL_BONUS_PER_ROUND,
            over_alloc_penalty_val=cfg.OVER_ALLOC_PENALTY,
            under_alloc_penalty_val=cfg.UNDER_ALLOC_PENALTY,
            critical_penalty_val=cfg.CRITICAL_PENALTY,
        )

        year, quarter = self._time_display()

        return StepResult(
            round_num=self._round,
            year=year,
            quarter=quarter,
            treasury=self._treasury.balance,
            allocations=alloc,
            revenue_factors={n: 0.0 for n in self._sectors},
            revenues={n: 0.0 for n in self._sectors},
            consumptions={n: 0.0 for n in self._sectors},
            demands={n: s.demand for n, s in self._sectors.items()},
            total_revenue=0.0,
            total_allocation=total_alloc,
            surplus_returned=0.0,
            population=self._population.value,
            productivity=self._productivity.value,
            reward=reward,
            events=events,
            crisis_occurred=crisis,
            done=True,
            termination_reason=reason,
        )

    def _build_observation(self, events: list[Event], crisis: bool) -> dict:
        """Build an observation dict for the initial state (after reset)."""
        return {
            "round_num": self._round,
            "year": 1,
            "quarter": 1,
            "treasury": self._treasury.balance,
            "population": self._population.value,
            "productivity": self._productivity.value,
            "sectors": {n: s.to_dict() for n, s in self._sectors.items()},
            "events": [e.to_dict() for e in events],
            "crisis_occurred": crisis,
            "done": False,
            "termination_reason": None,
        }

    def _time_display(self) -> tuple[int, int]:
        """Convert round number to (year, quarter)."""
        year = (self._round - 1) // 4 + 1
        quarter = (self._round - 1) % 4 + 1
        return year, quarter
