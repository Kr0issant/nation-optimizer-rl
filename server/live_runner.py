"""Live LLM-driven episode runner that emits visualizer-ready round records.

The :class:`LiveRunManager` is used by :mod:`server.visualizer_server` to spawn
inference episodes in background threads and stream their per-round JSON
records (in the schema documented in ``visualizer/EPISODE_FORMAT.md``) to the
React dashboard via Server-Sent Events.

The orchestration reuses :class:`server.environment.NationEnvironment` for its
9-phase parliamentary loop and retry handling. We subclass it as
:class:`RecordingEnvironment` so that we can:

1. Capture each agent action (debate / proposal / vote / abstain) as it is
   submitted, before the engine clears per-round state.
2. Snapshot the final per-sector state right after Phase 8 (surplus rollover)
   and before Phase 9 (termination check) — Phase 9 increments the round and
   calls ``_start_round`` for the next round, which wipes ``current_events``
   and resets ``Sector`` per-round fields.
3. On critical-failure rounds, snapshot allocations and events from the
   ``BUDGET_EXECUTION`` phase, where the engine flags the failure and zeroes
   out the would-be revenue.

The record shape mirrors the per-round contract in
``visualizer/EPISODE_FORMAT.md``; the front-end's ``normalizeEpisode`` helper
fills in any optional fields that change in the future.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from queue import Empty, Queue
from typing import Any, Optional

from agents.base import PolicyAdapter
from core.config import GameConfig
from core.events import Event
from core.game import Proposal
from llm_integration.adapters.parliamentary import ParliamentaryLLMAdapter
from llm_integration.hf_client import HuggingFaceTextGenerationClient
from schemas.observations import (
    Observation as DataclassObservation,
    OwnDepartmentObservation,
    ProposalObservation,
    VoteObservation,
)
from schemas.phases import Phase, valid_action_types_for_phase
from server.environment import NationEnvironment
from server.models import ParliamentaryAction, ParliamentaryObservation

LOG = logging.getLogger(__name__)


# ── Static config the visualizer expects up-front ───────────────────────────


def build_config_dict() -> dict[str, Any]:
    """Visualizer-shaped ``config`` block (matches ``EPISODE_FORMAT.md`` §1)."""
    cfg = GameConfig.from_json()
    sectors = []
    for name, baseline in cfg.SECTOR_BASELINES.items():
        meta = cfg.SECTOR_META.get(name, {})
        sectors.append(
            {
                "name": name,
                "full_name": meta.get("full_name", name),
                "baseline": baseline,
            }
        )
    return {
        "sectors": sectors,
        "pop_0": cfg.POP_0,
        "initial_treasury": cfg.INITIAL_TREASURY,
        "baseline_tax": cfg.BASELINE_TAX,
        "productivity_bounds": [cfg.PRODUCTIVITY_MIN, cfg.PRODUCTIVITY_MAX],
        "max_rounds": cfg.MAX_ROUNDS,
    }


# ── Adapter factory ─────────────────────────────────────────────────────────


def make_adapter(
    mode: str,
    *,
    model_id: str | None = None,
    token: str | None = None,
    temperature: float = 0.2,
) -> PolicyAdapter:
    """Build a :class:`PolicyAdapter` for the requested inference mode.

    ``mode`` values:
      - ``"llm"`` — Hugging Face Inference API (requires ``model_id`` + token).
      - ``"equal_split"`` / ``"optimal_zone"`` / ``"conservative"`` —
        rule-based baselines (no credentials needed; useful for local demos).
    """
    if mode == "llm":
        if not model_id:
            raise ValueError(
                "LLM mode requires model_id (set HF_MODEL_ID or pass model_id=...)."
            )
        client = HuggingFaceTextGenerationClient(
            model=model_id,
            token=token,
            temperature=temperature,
        )
        return ParliamentaryLLMAdapter(client=client, model=model_id)

    if mode == "equal_split":
        from agents.rule_based.equal_split import EqualSplitAdapter

        return EqualSplitAdapter()
    if mode == "optimal_zone":
        from agents.rule_based.optimal_zone import OptimalZoneAdapter

        return OptimalZoneAdapter()
    if mode == "conservative":
        from agents.rule_based.conservative import ConservativeAdapter

        return ConservativeAdapter()
    if mode == "greedy":
        from agents.rule_based.greedy import GreedyAdapter

        return GreedyAdapter()

    raise ValueError(f"Unknown adapter mode: {mode!r}")


# ── Round capture state ─────────────────────────────────────────────────────


@dataclass
class _RoundBuilder:
    """Mutable accumulator for a single round's visualizer record."""

    round_num: int
    treasury_before: float
    events: list[dict] = field(default_factory=list)
    crisis_occurred: bool = False
    debate: list[dict] = field(default_factory=list)


# ── Recording environment ───────────────────────────────────────────────────


class RecordingEnvironment(NationEnvironment):
    """:class:`NationEnvironment` that emits visualizer-shaped round records.

    Round records are pushed to ``on_round_complete`` once Phase 9 finishes
    (or earlier on critical failure). The schema matches
    ``visualizer/EPISODE_FORMAT.md``.

    Intermediate ``on_activity`` events are emitted *during* the round so the
    frontend can render debate messages, proposals, and votes as they happen.
    """

    def __init__(
        self,
        *,
        seed: int | None = None,
        on_round_complete: Callable[[dict[str, Any]], None],
        on_activity: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        super().__init__(seed=seed)
        self.on_round_complete = on_round_complete
        self.on_activity = on_activity or (lambda _: None)
        self._sector_names: list[str] = list(self.game.config.SECTOR_ORDER)
        self._builder: _RoundBuilder | None = None
        self._n_proposals_seen: int = 0
        self._n_votes_seen: int = 0

    # ── Lifecycle hooks ─────────────────────────────────────────────────

    def reset(self, seed: int | None = None, **kwargs: Any):  # type: ignore[override]
        obs, info = super().reset(seed=seed, **kwargs)
        self._begin_round(self.game.round)
        return obs, info

    def step(self, action: ParliamentaryAction):  # type: ignore[override]
        round_num = self._builder.round_num if self._builder else self.game.round

        # Capture debate messages eagerly and push to the live stream.
        if (
            self._builder is not None
            and action.type == "DEBATE"
            and (action.message or "").strip()
        ):
            msg = {
                "agent_id": action.agent_id,
                "department": action.agent_id,
                "message": (action.message or "").strip(),
            }
            self._builder.debate.append(msg)
            self.on_activity({
                "kind": "debate",
                "round_num": round_num,
                **msg,
            })

        result = super().step(action)

        # Emit activity events for any new proposals/votes the engine added
        # during this step.  We use persistent counters because _run_system_phases
        # (called inside super().step for the last vote of a round) clears the
        # game's proposals/votes lists — the counters let us catch up in
        # _flush_remaining_activities() for that edge case.
        self._emit_new_proposals(round_num)
        self._emit_new_votes(round_num)

        return result

    def _emit_new_proposals(self, round_num: int) -> None:
        new = self.game.proposals[self._n_proposals_seen:]
        for p in new:
            self.on_activity({
                "kind": "proposal",
                "round_num": round_num,
                **_proposal_to_view(p),
            })
        self._n_proposals_seen += len(new)

    def _emit_new_votes(self, round_num: int) -> None:
        new = self.game.votes[self._n_votes_seen:]
        for v in new:
            self.on_activity({
                "kind": "vote",
                "round_num": round_num,
                **_vote_to_view(v),
            })
        self._n_votes_seen += len(new)

    # ── Override system-phase loop to snapshot data before round flips ──

    def _run_system_phases(self, last_agent_id: str):  # type: ignore[override]
        """Run phases 5–9 manually so we can snapshot the round before reset."""
        round_num = self._builder.round_num if self._builder else self.game.round

        # The step that triggered us may have added the final vote(s) to the
        # game lists.  Emit activity events now, before _start_round() clears
        # them during phase 9.
        self._emit_new_proposals(round_num)
        self._emit_new_votes(round_num)

        # Voting has just transitioned to BUDGET_EXECUTION via _advance_phase;
        # proposal statuses + vote tallies are now final. Snapshot them before
        # any mutation in the BUDGET_EXECUTION step.
        proposals_view: list[dict] = []
        votes_view: list[dict] = []
        if self._builder is not None:
            proposals_view = [_proposal_to_view(p) for p in self.game.proposals]
            votes_view = [_vote_to_view(v) for v in self.game.votes]

        result = None
        sector_snapshot: dict[str, dict] | None = None
        treasury_after_value: float | None = None
        events_for_round: list[Event] = list(self.game.current_events)
        critical_failure_in_budget = False

        while not self.game.done and self.game.phase in (
            Phase.BUDGET_EXECUTION,
            Phase.CONSUMPTION_AND_EVENT_IMPACT,
            Phase.REVENUE_CALCULATION,
            Phase.SURPLUS_ROLLOVER,
            Phase.TERMINATION_CHECK,
        ):
            phase_before = self.game.phase
            result = self.game.step(None)

            # Critical failure inside BUDGET_EXECUTION ends the loop. The
            # engine has already zeroed revenue/consumption and set done=True.
            if phase_before == Phase.BUDGET_EXECUTION and self.game.done:
                critical_failure_in_budget = True
                sector_snapshot = {
                    n: dict(s.to_dict()) for n, s in self.game.sectors.items()
                }
                treasury_after_value = float(self.game.treasury.balance)
                break

            # After SURPLUS_ROLLOVER step, phase is now TERMINATION_CHECK and
            # per-sector data is final (allocation/revenue/consumption all set,
            # treasury credited with revenue + surplus + tax). The next step
            # will run TERMINATION_CHECK and (if game continues) call
            # ``_start_round`` which clears these fields.
            if phase_before == Phase.SURPLUS_ROLLOVER and not self.game.done:
                sector_snapshot = {
                    n: dict(s.to_dict()) for n, s in self.game.sectors.items()
                }
                treasury_after_value = float(self.game.treasury.balance)

        # Build & emit the round record.
        if self._builder is not None:
            try:
                self._finalize_round(
                    proposals_view=proposals_view,
                    votes_view=votes_view,
                    events_for_round=events_for_round,
                    sector_snapshot=sector_snapshot,
                    treasury_after_value=treasury_after_value,
                    critical_failure_in_budget=critical_failure_in_budget,
                    result=result,
                )
            except Exception:  # pragma: no cover - logged for debugging
                LOG.exception("Failed to build round record")

        # Mirror the post-loop bookkeeping that NationEnvironment._run_system_phases
        # would do (round reward + observation for the next agent).
        if result is not None:
            self._round_reward = result.reward.total

        if self.game.done:
            obs = self._build_observation(agent_id=last_agent_id)
            return obs, self._round_reward, True, False, self._build_info(result)

        if self.game.phase == Phase.EVENT_REVELATION:
            self.game.phase = Phase.DEBATE
        self._retry_count = 0
        # Begin capturing the new round (events are now in current_events).
        self._begin_round(self.game.round)
        next_agent = self._determine_next_agent()
        obs = self._build_observation(agent_id=next_agent)
        return obs, self._round_reward, False, False, self._build_info(result)

    # ── Internal helpers ────────────────────────────────────────────────

    def _begin_round(self, round_num: int) -> None:
        treasury_before = float(self.game.treasury.balance)
        builder = _RoundBuilder(
            round_num=round_num,
            treasury_before=treasury_before,
            crisis_occurred=bool(getattr(self.game, "current_round_crisis", False)),
        )
        builder.events = [
            _event_to_view(ev, round_num) for ev in self.game.current_events
        ]
        self._builder = builder
        self._n_proposals_seen = 0
        self._n_votes_seen = 0

        self.on_activity({
            "kind": "round_start",
            "round_num": round_num,
            "treasury_before": treasury_before,
            "events": list(builder.events),
            "crisis_occurred": builder.crisis_occurred,
        })

    def _finalize_round(
        self,
        *,
        proposals_view: list[dict],
        votes_view: list[dict],
        events_for_round: list[Event],
        sector_snapshot: dict[str, dict] | None,
        treasury_after_value: float | None,
        critical_failure_in_budget: bool,
        result: Any,
    ) -> None:
        builder = self._builder
        if builder is None:
            return

        sectors = sector_snapshot or {}
        allocations: dict[str, float] = {}
        revenues: dict[str, float] = {}
        rfs: dict[str, float] = {}
        consumptions: dict[str, float] = {}
        thresholds: dict[str, dict[str, float]] = {}
        for name in self._sector_names:
            s = sectors.get(name, {})
            allocations[name] = float(s.get("allocation", 0.0) or 0.0)
            revenues[name] = float(s.get("revenue", 0.0) or 0.0)
            rfs[name] = float(s.get("revenue_factor", 0.0) or 0.0)
            consumptions[name] = float(s.get("consumption", 0.0) or 0.0)
            thresholds[name] = {
                "critical": float(s.get("critical", 0.0) or 0.0),
                "demand": float(s.get("demand", 0.0) or 0.0),
                "surplus": float(s.get("surplus", 0.0) or 0.0),
                "wastage": float(s.get("wastage", 0.0) or 0.0),
            }

        events_view = [
            _event_to_view(ev, builder.round_num) for ev in events_for_round
        ]

        event_multipliers = {n: 1.0 for n in self._sector_names}
        for ev in events_for_round:
            for sname, mult in (ev.affected_sectors or {}).items():
                if sname in event_multipliers:
                    event_multipliers[sname] *= float(mult)

        total_allocation = sum(allocations.values())
        total_revenue = sum(revenues.values())
        surplus_returned = sum(
            max(0.0, allocations[n] - consumptions[n]) for n in self._sector_names
        )

        vote_results = _vote_results_from_proposals(proposals_view)
        proposal_order = _rotating_order(self._sector_names, builder.round_num)

        treasury_after = (
            float(treasury_after_value)
            if treasury_after_value is not None
            else float(self.game.treasury.balance)
        )

        reward_dict = (
            result.reward.to_dict()
            if result is not None and result.reward is not None
            else self.game.last_reward.to_dict()
        )

        record: dict[str, Any] = {
            "round_num": builder.round_num,
            "year": (builder.round_num - 1) // 4 + 1,
            "quarter": (builder.round_num - 1) % 4 + 1,
            "events": events_view,
            "crisis_occurred": bool(builder.crisis_occurred),
            "treasury_injection": sum(
                float(ev.get("treasury_injection", 0.0) or 0.0) for ev in events_view
            ),
            "debate": list(builder.debate),
            "proposal_order": proposal_order,
            "proposals": proposals_view,
            "votes": votes_view,
            "vote_results": vote_results,
            "allocations": allocations,
            "consumptions": consumptions,
            "revenues": revenues,
            "revenue_factors": rfs,
            "thresholds": thresholds,
            "event_multipliers": event_multipliers,
            "treasury_before": float(builder.treasury_before),
            "treasury_after": treasury_after,
            "total_allocation": float(total_allocation),
            "total_revenue": float(total_revenue),
            "surplus_returned": float(surplus_returned),
            "population": int(self.game.population.value),
            "productivity": float(self.game.productivity.value),
            "avg_revenue_factor": (
                sum(rfs.values()) / len(rfs) if rfs else 0.0
            ),
            "prosperity": (
                total_revenue / max(int(self.game.population.value), 1)
            ),
            "reward": reward_dict,
            "cumulative_reward": float(self.game.total_reward),
            "done": bool(self.game.done),
            "termination_reason": self.game.termination_reason,
            "critical_failure_in_budget": bool(critical_failure_in_budget),
        }

        self._builder = None
        self.on_round_complete(record)


# ── Adapter / engine schema helpers ─────────────────────────────────────────


def _proposal_to_view(p: Proposal) -> dict[str, Any]:
    return {
        "proposal_id": p.proposal_id,
        "agent_id": p.agent_id,
        "department": p.department,
        "amount": float(p.amount),
        "justification": p.justification or "",
        "status": p.status,
        "rejection_reason": p.rejection_reason,
        "votes": dict(p.votes),
    }


def _find_vote_target(proposals: list, agent_id: str) -> str | None:
    """Return the proposal_id that *agent_id* should vote on next, or None."""
    for p in proposals:
        if (
            p.status == "pending"
            and p.agent_id != agent_id
            and p.department != agent_id
            and agent_id not in p.votes
        ):
            return p.proposal_id
    return None


def _vote_to_view(v: dict[str, Any]) -> dict[str, Any]:
    aid = v.get("agent_id", "")
    return {
        "proposal_id": v.get("proposal_id", ""),
        "agent_id": aid,
        # In parliamentary mode each minister IS a department, so we expose
        # both keys to keep the visualizer chip rendering happy.
        "department": aid,
        "vote": v.get("vote", "ABSTAIN"),
    }


def _vote_results_from_proposals(proposals_view: list[dict]) -> list[dict]:
    """Roll up per-proposal vote tallies and map engine status → UI status."""
    out: list[dict] = []
    for p in proposals_view:
        votes = (p.get("votes") or {}).values()
        yes = sum(1 for v in votes if v == "YES")
        no = sum(1 for v in votes if v == "NO")
        ab = sum(1 for v in votes if v == "ABSTAIN")
        engine_status = p.get("status", "pending")
        ui_status = {
            "approved": "APPROVED",
            "rejected": "REJECTED",
            "rejected_invalid": "AUTO_REJECTED_INVALID",
            "pending": "PENDING",
        }.get(engine_status, engine_status.upper())
        if (
            engine_status == "rejected"
            and p.get("rejection_reason") == "exceeds_remaining_treasury"
        ):
            ui_status = "AUTO_REJECTED_INSUFFICIENT_TREASURY"
        out.append(
            {
                "proposal_id": p["proposal_id"],
                "department": p["department"],
                "amount": float(p["amount"]),
                "yes": yes,
                "no": no,
                "abstain": ab,
                "status": ui_status,
            }
        )
    return out


def _rotating_order(sector_names: list[str], round_num: int) -> list[str]:
    if not sector_names:
        return []
    n = len(sector_names)
    start = (round_num - 1) % n
    return sector_names[start:] + sector_names[:start]


def parliamentary_obs_to_dataclass(
    obs: ParliamentaryObservation,
) -> DataclassObservation:
    """Convert the Pydantic ``ParliamentaryObservation`` into the dataclass
    ``schemas.observations.Observation`` consumed by every PolicyAdapter.

    The adapters (``EqualSplitAdapter``, ``ParliamentaryLLMAdapter``, …) and
    the prompt builder (``llm_integration.prompts.minister``) call
    ``dataclasses.asdict`` on proposal/vote items, which only works on real
    dataclasses. ``NationEnvironment`` returns Pydantic models, so we map them
    once per agent action.
    """
    own_pyd = obs.own_department
    own = OwnDepartmentObservation(
        name=getattr(own_pyd, "name", obs.current_agent or ""),
        allocated_budget=getattr(own_pyd, "allocated_budget", None) if own_pyd else None,
        consumption=getattr(own_pyd, "consumption", None) if own_pyd else None,
        surplus=getattr(own_pyd, "surplus", None) if own_pyd else None,
        efficiency_rating=getattr(own_pyd, "efficiency_rating", None) if own_pyd else None,
        treasury_surplus_returned_this_round=(
            getattr(own_pyd, "treasury_surplus_returned_this_round", None)
            if own_pyd
            else None
        ),
    )

    proposals = tuple(
        ProposalObservation(
            proposal_id=p.proposal_id,
            department=p.department,
            amount=float(p.amount),
            status=p.status or "pending",
            agent_id=p.agent_id,
            votes=dict(p.votes or {}),
        )
        for p in (obs.proposals or [])
    )

    votes = tuple(
        VoteObservation(
            proposal_id=v.proposal_id,
            agent_id=v.agent_id,
            vote=v.vote,
        )
        for v in (obs.votes or [])
    )

    debate = tuple(
        {str(k): str(v) for k, v in (msg or {}).items()}
        for msg in (obs.debate_messages or [])
    )

    event_ledger = tuple(dict(ev) for ev in (obs.event_ledger or []))

    try:
        phase_enum = Phase(int(obs.phase))
    except (ValueError, TypeError):
        phase_enum = Phase.DEBATE

    return DataclassObservation(
        round=int(obs.round or 0),
        phase=phase_enum,
        treasury=float(obs.treasury or 0.0),
        own_department=own,
        event_ledger=event_ledger,
        proposals=proposals,
        votes=votes,
        debate_messages=debate,
        termination=dict(obs.termination or {}),
    )


def _event_to_view(ev: Any, round_num: int) -> dict[str, Any]:
    """Normalise either a core ``Event`` or a dict into the viewer schema."""
    if isinstance(ev, Event):
        affected = dict(ev.affected_sectors)
        treasury_injection = float(getattr(ev, "_treasury_injection", 0.0) or 0.0)
        category = ev.category
        narrative = ev.narrative or ev.description or ""
        ev_dict = {
            "id": ev.id,
            "name": ev.name,
            "severity": int(ev.severity),
            "category": category,
            "narrative": narrative,
        }
    else:
        ev_dict = dict(ev)
        affected = ev_dict.get("affected_sectors") or ev_dict.get(
            "affected_departments"
        ) or {}
        if not isinstance(affected, dict):
            affected = {}
        treasury_injection = float(ev_dict.get("treasury_injection", 0.0) or 0.0)
        category = ev_dict.get("category", "")
        narrative = ev_dict.get("narrative") or ev_dict.get("description") or ""

    multipliers = [float(v) for v in affected.values()]
    is_positive = (
        category == "positive"
        or treasury_injection > 0
        or (bool(multipliers) and all(m < 1 for m in multipliers))
    )

    return {
        "round": round_num,
        "id": ev_dict.get("id", ""),
        "name": ev_dict.get("name", ""),
        "severity": int(ev_dict.get("severity", 0) or 0),
        "category": category,
        "narrative": narrative,
        "affected_sectors": affected,
        "treasury_injection": treasury_injection,
        "is_positive": bool(is_positive),
    }


# ── Per-run state and SSE event queue ───────────────────────────────────────


@dataclass
class LiveRun:
    """In-process record of a streaming inference episode."""

    run_id: str
    seed: int
    policy: str
    config: dict[str, Any]
    mode: str
    model_id: str | None
    max_rounds: int
    rounds: list[dict[str, Any]] = field(default_factory=list)
    summary: Optional[dict[str, Any]] = None
    state: str = "pending"  # pending | running | done | error
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)

    # Each subscriber gets its own queue so multiple browser tabs can stream
    # the same run independently.
    _subscribers: list["Queue[dict[str, Any]]"] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _history: list[dict[str, Any]] = field(default_factory=list)
    _closed: bool = False

    def subscribe(self) -> "Queue[dict[str, Any]]":
        q: Queue[dict[str, Any]] = Queue()
        with self._lock:
            # Replay all events seen so far so late joiners get the full picture.
            for ev in self._history:
                q.put(ev)
            if not self._closed:
                self._subscribers.append(q)
            else:
                q.put({"type": "done", "data": {"reason": "already_closed"}})
        return q

    def unsubscribe(self, q: "Queue[dict[str, Any]]") -> None:
        with self._lock:
            if q in self._subscribers:
                self._subscribers.remove(q)

    def emit(self, event: dict[str, Any]) -> None:
        with self._lock:
            self._history.append(event)
            for q in list(self._subscribers):
                q.put(event)

    def close(self) -> None:
        with self._lock:
            self._closed = True
            for q in list(self._subscribers):
                q.put({"type": "done", "data": {"reason": "complete"}})
            self._subscribers.clear()

    def snapshot(self) -> dict[str, Any]:
        """Return the full episode-so-far in viewer JSON shape."""
        with self._lock:
            return {
                "episode_id": self.run_id,
                "seed": self.seed,
                "policy": self.policy,
                "config": self.config,
                "rounds": list(self.rounds),
                "summary": self.summary,
                "state": self.state,
                "error": self.error,
                "mode": self.mode,
                "model_id": self.model_id,
                "max_rounds": self.max_rounds,
            }


# ── Manager ─────────────────────────────────────────────────────────────────


class LiveRunManager:
    """Spawns and tracks live inference runs; one instance per server process."""

    def __init__(self, *, max_runs_kept: int = 16) -> None:
        self._runs: dict[str, LiveRun] = {}
        self._order: list[str] = []
        self._lock = threading.Lock()
        self._max_runs_kept = max_runs_kept

    def list_runs(self) -> list[dict[str, Any]]:
        with self._lock:
            return [
                {
                    "run_id": r.run_id,
                    "policy": r.policy,
                    "state": r.state,
                    "mode": r.mode,
                    "seed": r.seed,
                    "rounds": len(r.rounds),
                    "created_at": r.created_at,
                }
                for r in self._runs.values()
            ]

    def get(self, run_id: str) -> LiveRun | None:
        with self._lock:
            return self._runs.get(run_id)

    def create(
        self,
        *,
        mode: str,
        model_id: str | None,
        seed: int,
        max_rounds: int,
        temperature: float,
        token: str | None = None,
    ) -> LiveRun:
        config = build_config_dict()
        run = LiveRun(
            run_id=uuid.uuid4().hex[:12],
            seed=seed,
            policy=mode if mode != "llm" else (model_id or "huggingface"),
            config=config,
            mode=mode,
            model_id=model_id,
            max_rounds=max_rounds,
        )
        with self._lock:
            self._runs[run.run_id] = run
            self._order.append(run.run_id)
            while len(self._order) > self._max_runs_kept:
                old_id = self._order.pop(0)
                old = self._runs.pop(old_id, None)
                if old is not None:
                    old.close()

        thread = threading.Thread(
            target=self._worker,
            args=(run, mode, model_id, token, max_rounds, temperature),
            daemon=True,
            name=f"live-run-{run.run_id}",
        )
        thread.start()
        return run

    # ── Worker thread ──────────────────────────────────────────────────

    def _worker(
        self,
        run: LiveRun,
        mode: str,
        model_id: str | None,
        token: str | None,
        max_rounds: int,
        temperature: float,
    ) -> None:
        try:
            run.state = "running"
            run.emit(
                {
                    "type": "start",
                    "data": {
                        "run_id": run.run_id,
                        "policy": run.policy,
                        "mode": mode,
                        "seed": run.seed,
                        "config": run.config,
                        "max_rounds": max_rounds,
                    },
                }
            )

            adapter = make_adapter(
                mode,
                model_id=model_id,
                token=token,
                temperature=temperature,
            )

            def on_round_complete(record: dict[str, Any]) -> None:
                run.rounds.append(record)
                run.emit({"type": "round", "data": record})

            def on_activity(event: dict[str, Any]) -> None:
                run.emit({"type": "activity", "data": event})

            env = RecordingEnvironment(
                seed=run.seed,
                on_round_complete=on_round_complete,
                on_activity=on_activity,
            )
            obs, _ = env.reset()

            steps = 0
            # Hard safety cap: one round can take roughly
            #   debate(6) + propose(6) + vote(~30) + retries(<=2x) ~= 100 actions.
            max_steps = max_rounds * 200

            n_departments = len(env.departments)
            current_round = env.game.round
            debates_this_round = 0
            stale_agent: str | None = None
            stale_count = 0
            MAX_STALE = n_departments * 3

            while (
                not env.game.done
                and len(run.rounds) < max_rounds
                and steps < max_steps
            ):
                steps += 1
                current_agent = obs.current_agent
                if not current_agent:
                    LOG.warning("No current_agent on obs; aborting run.")
                    break

                valid_actions = (
                    list(obs.valid_actions)
                    if obs.valid_actions
                    else list(valid_action_types_for_phase(Phase(obs.phase)))
                )

                if env.game.round != current_round:
                    current_round = env.game.round
                    debates_this_round = 0
                    stale_agent = None
                    stale_count = 0

                phase_now = Phase(int(obs.phase))

                # ── Stale-loop detection ──
                # If the same agent keeps being selected without progress,
                # inject a direct action to break the deadlock.
                if current_agent == stale_agent:
                    stale_count += 1
                else:
                    stale_agent = current_agent
                    stale_count = 1

                force_direct = stale_count > MAX_STALE

                if (
                    phase_now == Phase.DEBATE
                    and debates_this_round >= n_departments
                ):
                    p_action = ParliamentaryAction(
                        agent_id=current_agent,
                        type="FINISH_DEBATE",
                        reason="All ministers have spoken.",
                    )
                elif force_direct and phase_now == Phase.VOTING:
                    # Find the proposal this agent needs to vote on and
                    # force a YES vote to break the loop.
                    target_pid = _find_vote_target(
                        env.game.proposals, current_agent,
                    )
                    if target_pid:
                        LOG.warning(
                            "Stale loop on %s voting; forcing YES on %s",
                            current_agent,
                            target_pid,
                        )
                        p_action = ParliamentaryAction(
                            agent_id=current_agent,
                            type="VOTE",
                            proposal_id=target_pid,
                            vote="YES",
                        )
                    else:
                        LOG.warning(
                            "Stale loop on %s voting but no target; skipping",
                            current_agent,
                        )
                        break
                else:
                    dc_obs = parliamentary_obs_to_dataclass(obs)
                    action = adapter.act(
                        observation=dc_obs,
                        valid_actions=valid_actions,
                        agent_id=current_agent,
                    )
                    action_dict = action.to_dict()
                    action_dict["agent_id"] = current_agent
                    p_action = ParliamentaryAction(**action_dict)
                    if phase_now == Phase.DEBATE:
                        if p_action.type == "FINISH_DEBATE":
                            debates_this_round = n_departments
                        elif (
                            p_action.type == "DEBATE"
                            and (p_action.message or "").strip()
                        ):
                            debates_this_round += 1

                obs, _, _, _, _ = env.step(p_action)

            if run.rounds:
                last = run.rounds[-1]
                pop = max(int(last.get("population") or 1), 1)
                final_prosperity = (
                    float(last.get("treasury_after") or 0.0)
                    + float(last.get("total_revenue") or 0.0)
                ) / pop
                run.summary = {
                    "rounds_survived": int(last["round_num"]),
                    "total_reward": float(last["cumulative_reward"]),
                    "final_treasury": float(last["treasury_after"]),
                    "final_prosperity": float(final_prosperity),
                    "final_productivity": float(last["productivity"]),
                    "final_population": int(last["population"]),
                    "termination_reason": last.get("termination_reason"),
                }
                run.emit({"type": "summary", "data": run.summary})

            run.state = "done"
            run.emit({"type": "done", "data": {"reason": "complete"}})
        except Exception as exc:  # pragma: no cover - surfaced to UI
            LOG.exception("Live run failed")
            run.state = "error"
            run.error = str(exc)
            run.emit({"type": "error", "data": {"message": str(exc)}})
            run.emit({"type": "done", "data": {"reason": "error"}})
        finally:
            run.close()


__all__ = [
    "LiveRun",
    "LiveRunManager",
    "RecordingEnvironment",
    "build_config_dict",
    "make_adapter",
    "parliamentary_obs_to_dataclass",
]
