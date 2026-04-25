"""NationGame orchestration for the phased core game loop."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Iterable, Mapping

from schemas.actions import ActionType, VoteChoice
from schemas.phases import Phase, valid_action_types_for_phase

from .config import DEFAULT_CONFIG, GameConfig
from .events import Event, EventEngine
from .population import PopulationTracker
from .productivity import ProductivityTracker
from .reward import RewardBreakdown, compute_reward
from .sector import Sector
from .treasury import Treasury


PHASE_COUNT = 9
PROPOSAL_STATUS_PENDING = "pending"
PROPOSAL_STATUS_APPROVED = "approved"
PROPOSAL_STATUS_REJECTED = "rejected"
PROPOSAL_STATUS_REJECTED_INVALID = "rejected_invalid"
TERMINATION_CRITICAL_FAILURE = "CRITICAL_FAILURE"
TERMINATION_BANKRUPTCY = "BANKRUPTCY"
TERMINATION_SHUTDOWN = "SHUTDOWN"
TERMINATION_MAX_ROUNDS = "MAX_ROUNDS"
TERMINATION_PROSPERITY = "PROSPERITY_THRESHOLD"


@dataclass
class Proposal:
    """Public budget proposal submitted during phase 3."""

    proposal_id: str
    agent_id: str
    department: str
    amount: float
    justification: str = ""
    status: str = PROPOSAL_STATUS_PENDING
    votes: dict[str, str] = field(default_factory=dict)
    rejection_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "agent_id": self.agent_id,
            "department": self.department,
            "amount": self.amount,
            "justification": self.justification,
            "status": self.status,
            "votes": dict(self.votes),
            "rejection_reason": self.rejection_reason,
        }


@dataclass
class StepResult:
    """Result returned by :meth:`NationGame.step`."""

    observation: dict[str, Any]
    reward: RewardBreakdown
    done: bool
    info: dict[str, Any] = field(default_factory=dict)

    @property
    def round_num(self) -> int:
        return self.observation["round"]

    @property
    def termination_reason(self) -> str | None:
        return self.info.get("termination_reason")

    @property
    def treasury(self) -> float:
        return self.observation["treasury"]

    @property
    def productivity(self) -> float:
        return self.observation["productivity"]

    @property
    def population(self) -> int:
        return self.observation["population"]

    @property
    def year(self) -> int:
        return self.observation["year"]

    @property
    def quarter(self) -> int:
        return self.observation["quarter"]

    @property
    def allocations(self) -> dict[str, float]:
        return {
            name: sector["allocation"]
            for name, sector in self.observation["sectors"].items()
        }

    @property
    def revenue_factors(self) -> dict[str, float]:
        return {
            name: sector["revenue_factor"]
            for name, sector in self.observation["sectors"].items()
        }

    @property
    def revenues(self) -> dict[str, float]:
        return {
            name: sector["revenue"]
            for name, sector in self.observation["sectors"].items()
        }

    @property
    def consumptions(self) -> dict[str, float]:
        return {
            name: sector["consumption"]
            for name, sector in self.observation["sectors"].items()
        }

    @property
    def demands(self) -> dict[str, float]:
        return {
            name: sector["demand"]
            for name, sector in self.observation["sectors"].items()
        }

    @property
    def total_revenue(self) -> float:
        return self.observation["last_total_revenue"]

    @property
    def total_allocation(self) -> float:
        return self.observation["last_total_allocation"]

    @property
    def surplus_returned(self) -> float:
        return self.observation["last_total_surplus"]

    @property
    def events(self) -> list[dict[str, Any]]:
        return self.observation["current_events"]

    @property
    def crisis_occurred(self) -> bool:
        return bool(self.info.get("crisis_occurred", False))

    def to_dict(self) -> dict[str, Any]:
        """Serialise the result for legacy callers and environment wrappers."""
        return {
            **self.observation,
            "round_num": self.round_num,
            "allocations": self.allocations,
            "revenue_factors": self.revenue_factors,
            "revenues": self.revenues,
            "consumptions": self.consumptions,
            "demands": self.demands,
            "total_revenue": self.total_revenue,
            "total_allocation": self.total_allocation,
            "surplus_returned": self.surplus_returned,
            "reward": self.reward.to_dict(),
            "done": self.done,
            "termination_reason": self.termination_reason,
        }


class NationGame:
    """Playable core game loop across the nine specified phases."""

    def __init__(self, config: GameConfig | None = None, seed: int | None = None) -> None:
        self.config = config or DEFAULT_CONFIG
        self._initial_seed = seed
        self.rng = random.Random(seed)
        self.event_engine = EventEngine(rng=self.rng)
        self.reset(seed=seed)

    def reset(self, seed: int | None = None) -> dict[str, Any]:
        """Start a new episode and reveal round 1 events."""
        if seed is not None:
            self._initial_seed = seed
            self.rng = random.Random(seed)
            self.event_engine = EventEngine(rng=self.rng)

        self.round = 1
        self.phase = Phase.EVENT_REVELATION
        self.done = False
        self.termination_reason: str | None = None
        self.total_reward = 0.0
        self.last_reward = compute_reward(prosperity=0.0)
        self.last_info: dict[str, Any] = {}
        self.shutdown_counter = 0
        self.prosperity_streak = 0
        self.last_total_revenue = 0.0
        self.last_total_surplus = 0.0
        self.last_total_allocation = 0.0
        self.current_round_crisis = False
        self.current_events: list[Event] = []
        self.event_ledger: list[dict[str, Any]] = []
        self.debate_messages: list[dict[str, str]] = []
        self.proposals: list[Proposal] = []
        self.votes: list[dict[str, str]] = []
        self._proposal_counter = 0
        self._submitted_departments: set[str] = set()
        self._abstained_departments: set[str] = set()

        self.treasury = Treasury(
            balance=self.config.INITIAL_TREASURY,
            baseline_tax=self.config.BASELINE_TAX,
        )
        self.population = PopulationTracker(
            value=self.config.POP_0,
            birth_rate_base=self.config.BIRTH_RATE_BASE,
            death_rate_base=self.config.DEATH_RATE_BASE,
            crisis_death_penalty=self.config.CRISIS_DEATH_PENALTY,
        )
        self.productivity = ProductivityTracker(
            value=self.config.INITIAL_PRODUCTIVITY,
            min_val=self.config.PRODUCTIVITY_MIN,
            max_val=self.config.PRODUCTIVITY_MAX,
            step=self.config.PRODUCTIVITY_STEP,
        )
        self.sectors = {
            name: Sector(
                name=name,
                baseline=baseline,
                full_name=self.config.SECTOR_META.get(name, {}).get("full_name", name),
                description=self.config.SECTOR_META.get(name, {}).get("description", ""),
                _critical_ratio=self.config.CRITICAL_RATIO,
                _surplus_ratio=self.config.SURPLUS_RATIO,
                _wastage_ratio=self.config.WASTAGE_RATIO,
                _rf_max=self.config.RF_MAX,
            )
            for name, baseline in self.config.SECTOR_BASELINES.items()
        }

        self._start_round()
        return self.state()

    def state(self) -> dict[str, Any]:
        """Return a structured public state snapshot."""
        year, quarter = self._year_quarter(self.round)
        return {
            "round": self.round,
            "phase": self.phase,
            "phase_name": self.phase.name,
            "year": year,
            "quarter": quarter,
            "treasury": round(self.treasury.balance, 6),
            "population": self.population.value,
            "productivity": round(self.productivity.value, 6),
            "sectors": {name: sector.to_dict() for name, sector in self.sectors.items()},
            "event_ledger": list(self.event_ledger),
            "current_events": [event.to_dict() for event in self.current_events],
            "debate_messages": list(self.debate_messages),
            "proposals": [proposal.to_dict() for proposal in self.proposals],
            "votes": list(self.votes),
            "termination": {
                "episode_ended": self.done,
                "reason": self.termination_reason,
            },
            "last_reward": self.last_reward.to_dict(),
            "total_reward": round(self.total_reward, 6),
            "last_total_revenue": round(self.last_total_revenue, 6),
            "last_total_surplus": round(self.last_total_surplus, 6),
            "last_total_allocation": round(self.last_total_allocation, 6),
        }

    def step(self, action: Any = None) -> StepResult:
        """
        Process one phase step.

        A mapping of ``{department: amount}`` remains supported as a legacy
        full-round shortcut and is converted into direct approved allocations.
        """
        if self.done:
            return self._result({"ignored": True, "reason": "episode_done"})

        if self._is_allocation_mapping(action):
            return self._run_direct_allocation_round(action)

        info: dict[str, Any] = {"accepted_actions": [], "ignored_actions": [], "rejected_actions": []}
        for item in self._normalize_actions(action):
            self._handle_phase_action(item, info)

        self._run_current_system_phase(info)
        completed_round = self.round
        self._advance_phase()

        if not self.done and self.phase == Phase.EVENT_REVELATION and self.round != completed_round:
            self._start_round()

        self.last_info = info
        return self._result(info)

    def _start_round(self) -> None:
        self.current_round_crisis = False
        self.current_events = []
        self.debate_messages = []
        self.proposals = []
        self.votes = []
        self._submitted_departments = set()
        self._abstained_departments = set()

        for sector in self.sectors.values():
            sector.reset_round()
            sector.update_thresholds(self.population.value, self.config.POP_0)

        self.current_events = self.event_engine.generate_events(
            sector_names=list(self.config.SECTOR_ORDER)
        )
        self.current_round_crisis = self.event_engine.apply_events(
            self.current_events,
            self.sectors,
            self.treasury,
        )
        for sector in self.sectors.values():
            sector.update_thresholds(self.population.value, self.config.POP_0)
        for event in self.current_events:
            record = event.to_dict()
            record["round"] = self.round
            self.event_ledger.append(record)

    def _handle_phase_action(self, action: Mapping[str, Any], info: dict[str, Any]) -> None:
        action_type = self._action_type_value(action.get("type"))
        if action_type not in valid_action_types_for_phase(self.phase):
            info["ignored_actions"].append({"action": dict(action), "reason": "wrong_phase"})
            return

        if action_type == ActionType.DEBATE.value:
            self._handle_debate(action, info)
        elif action_type == ActionType.PROPOSE_BUDGET.value:
            self._handle_proposal(action, info)
        elif action_type == ActionType.ABSTAIN_FROM_PROPOSAL.value:
            self._handle_proposal_abstention(action, info)
        elif action_type == ActionType.VOTE.value:
            self._handle_vote(action, info)

    def _handle_debate(self, action: Mapping[str, Any], info: dict[str, Any]) -> None:
        message = str(action.get("message", ""))
        agent_id = str(action.get("agent_id") or action.get("agent") or "anonymous")
        entry = {"agent_id": agent_id, "message": message}
        self.debate_messages.append(entry)
        info["accepted_actions"].append({"type": ActionType.DEBATE.value, **entry})

    def _handle_proposal(self, action: Mapping[str, Any], info: dict[str, Any]) -> None:
        department = str(action.get("department", ""))
        agent_id = str(action.get("agent_id") or action.get("agent") or department)
        amount = action.get("amount")

        if department in self._submitted_departments:
            info["ignored_actions"].append({"action": dict(action), "reason": "duplicate_proposal"})
            return

        rejection_reason = self._proposal_rejection_reason(agent_id, department, amount)
        if rejection_reason is not None:
            proposal = self._new_proposal(
                agent_id=agent_id,
                department=department,
                amount=self._safe_float(amount),
                justification=str(action.get("justification", "")),
                status=PROPOSAL_STATUS_REJECTED_INVALID,
                rejection_reason=rejection_reason,
            )
            info["rejected_actions"].append(
                {"action": dict(action), "reason": rejection_reason, "proposal_id": proposal.proposal_id}
            )
            return

        proposal = self._new_proposal(
            agent_id=agent_id,
            department=department,
            amount=float(amount),
            justification=str(action.get("justification", "")),
        )
        self._submitted_departments.add(department)
        info["accepted_actions"].append({"type": ActionType.PROPOSE_BUDGET.value, "proposal_id": proposal.proposal_id})

    def _handle_proposal_abstention(self, action: Mapping[str, Any], info: dict[str, Any]) -> None:
        department = str(action.get("department") or action.get("agent_id") or action.get("agent") or "")
        if department not in self.sectors or department in self._submitted_departments:
            info["ignored_actions"].append({"action": dict(action), "reason": "invalid_abstention"})
            return
        self._abstained_departments.add(department)
        info["accepted_actions"].append({"type": ActionType.ABSTAIN_FROM_PROPOSAL.value, "department": department})

    def _handle_vote(self, action: Mapping[str, Any], info: dict[str, Any]) -> None:
        proposal_id = str(action.get("proposal_id", ""))
        proposal = self._proposal_by_id(proposal_id)
        agent_id = str(action.get("agent_id") or action.get("agent") or "")
        vote = self._vote_value(action.get("vote"))

        if proposal is None or proposal.status != PROPOSAL_STATUS_PENDING:
            info["ignored_actions"].append({"action": dict(action), "reason": "proposal_not_votable"})
            return
        if not agent_id:
            info["ignored_actions"].append({"action": dict(action), "reason": "missing_agent_id"})
            return
        if agent_id == proposal.agent_id or agent_id == proposal.department:
            info["rejected_actions"].append({"action": dict(action), "reason": "self_vote"})
            return
        if vote is None:
            info["rejected_actions"].append({"action": dict(action), "reason": "invalid_vote"})
            return
        if agent_id in proposal.votes:
            info["ignored_actions"].append({"action": dict(action), "reason": "duplicate_vote"})
            return

        proposal.votes[agent_id] = vote
        self.votes.append({"proposal_id": proposal_id, "agent_id": agent_id, "vote": vote})
        info["accepted_actions"].append({"type": ActionType.VOTE.value, "proposal_id": proposal_id, "agent_id": agent_id, "vote": vote})

    def _run_current_system_phase(self, info: dict[str, Any]) -> None:
        if self.phase == Phase.BUDGET_EXECUTION:
            self._tally_votes()
            critical_failed = self._execute_approved_budgets()
            if critical_failed:
                self._finish_round(critical_failed=True, terminate_immediately=True)
                info["termination_reason"] = self.termination_reason
        elif self.phase == Phase.CONSUMPTION_AND_EVENT_IMPACT and not self.done:
            self._compute_consumption()
        elif self.phase == Phase.REVENUE_CALCULATION and not self.done:
            self._compute_revenue()
            self.treasury.credit(self.last_total_revenue)
        elif self.phase == Phase.SURPLUS_ROLLOVER and not self.done:
            self.treasury.credit(self.last_total_surplus)
            self.treasury.apply_baseline_tax()
        elif self.phase == Phase.TERMINATION_CHECK and not self.done:
            self._finish_round(critical_failed=False)
            info["termination_reason"] = self.termination_reason

    def _run_direct_allocation_round(self, allocations: Mapping[str, Any]) -> StepResult:
        if self.phase != Phase.EVENT_REVELATION:
            self.phase = Phase.EVENT_REVELATION
            self._start_round()

        for proposal in self.proposals:
            proposal.status = PROPOSAL_STATUS_REJECTED
        self.proposals = []
        for department in self.config.SECTOR_ORDER:
            amount = float(allocations.get(department, 0.0))
            proposal = self._new_proposal(
                agent_id=department,
                department=department,
                amount=amount,
                status=PROPOSAL_STATUS_APPROVED,
            )
            self.sectors[department].allocate(proposal.amount)

        critical_failed = any(sector.is_critical_failure(self.population.value) for sector in self.sectors.values())
        if not critical_failed:
            self.last_total_allocation = sum(sector.allocation for sector in self.sectors.values())
            self.treasury.balance -= self.last_total_allocation
            self._compute_consumption()
            self._compute_revenue()
            self.treasury.credit(self.last_total_revenue)
            self.treasury.credit(self.last_total_surplus)
            self.treasury.apply_baseline_tax()

        self._finish_round(critical_failed=critical_failed, completed_round=self.round)
        info = {
            "accepted_actions": [{"type": "DIRECT_ALLOCATION"}],
            "ignored_actions": [],
            "rejected_actions": [],
            "termination_reason": self.termination_reason,
        }
        self.last_info = info
        if not self.done:
            self.round += 1
            self.phase = Phase.EVENT_REVELATION
            self._start_round()
        return self._result(info, completed_round=self.round - 1 if not self.done else self.round)

    def _execute_approved_budgets(self) -> bool:
        for sector in self.sectors.values():
            sector.allocate(0.0)

        for proposal in self.proposals:
            if proposal.status == PROPOSAL_STATUS_APPROVED:
                self.sectors[proposal.department].allocate(
                    self.sectors[proposal.department].allocation + proposal.amount
                )

        approved_departments = {
            proposal.department
            for proposal in self.proposals
            if proposal.status == PROPOSAL_STATUS_APPROVED
        }
        critical_failed = any(
            sector.is_critical_failure(self.population.value)
            for sector in self.sectors.values()
        )
        if critical_failed:
            self.last_total_allocation = sum(sector.allocation for sector in self.sectors.values())
            return True

        self.last_total_allocation = 0.0
        for sector in self.sectors.values():
            self.last_total_allocation += sector.allocation
            self.treasury.debit(sector.allocation)
        return False

    def _tally_votes(self) -> None:
        remaining_treasury = self.treasury.balance
        for proposal in self.proposals:
            if proposal.status != PROPOSAL_STATUS_PENDING:
                continue
            yes_votes = sum(1 for vote in proposal.votes.values() if vote == VoteChoice.YES.value)
            no_votes = sum(1 for vote in proposal.votes.values() if vote == VoteChoice.NO.value)
            if proposal.amount > remaining_treasury:
                proposal.status = PROPOSAL_STATUS_REJECTED
                proposal.rejection_reason = "exceeds_remaining_treasury"
            elif yes_votes > no_votes:
                proposal.status = PROPOSAL_STATUS_APPROVED
                remaining_treasury -= proposal.amount
            else:
                proposal.status = PROPOSAL_STATUS_REJECTED

    def _compute_consumption(self) -> None:
        self.last_total_surplus = 0.0
        for sector in self.sectors.values():
            self.last_total_surplus += sector.compute_consumption()

    def _compute_revenue(self) -> None:
        self.last_total_revenue = 0.0
        for sector in self.sectors.values():
            revenue = sector.compute_revenue(self.population.value, self.productivity.value)
            if revenue is not None:
                self.last_total_revenue += revenue

    def _finish_round(
        self,
        *,
        critical_failed: bool,
        terminate_immediately: bool = False,
        completed_round: int | None = None,
    ) -> None:
        completed_round = completed_round or self.round
        if critical_failed:
            self.last_total_revenue = 0.0
            self.last_total_surplus = 0.0
            self.done = True
            self.termination_reason = TERMINATION_CRITICAL_FAILURE
        else:
            revenue_factors = [sector.revenue_factor_value for sector in self.sectors.values()]
            self.productivity.update(revenue_factors)
            self.population.update(self.productivity.value, self.current_round_crisis)
            self._update_shutdown_counter()
            self._check_standard_termination()

        prosperity = self.last_total_revenue / max(self.population.value, 1)
        zone_penalty_overrides = (
            {"over_allocated_count": 0, "under_allocated_count": 0}
            if critical_failed
            else {}
        )
        self.last_reward = compute_reward(
            sectors=self.sectors,
            total_revenue=self.last_total_revenue,
            population=self.population.value,
            productivity=self.productivity.value,
            round_num=completed_round,
            critical_failed=critical_failed,
            **zone_penalty_overrides,
            productivity_bonus_scale=self.config.PRODUCTIVITY_BONUS_SCALE,
            survival_bonus_per_round=self.config.SURVIVAL_BONUS_PER_ROUND,
            over_alloc_penalty_val=self.config.OVER_ALLOC_PENALTY,
            under_alloc_penalty_val=self.config.UNDER_ALLOC_PENALTY,
            critical_penalty_val=self.config.CRITICAL_PENALTY,
        )
        if self.termination_reason == TERMINATION_BANKRUPTCY:
            self.last_reward.critical_penalty = self.config.BANKRUPTCY_PENALTY
        self.total_reward += self.last_reward.total

        if terminate_immediately:
            self.phase = Phase.BUDGET_EXECUTION
        if not self.done and self.config.PROSPERITY_THRESHOLD is not None:
            if prosperity >= self.config.PROSPERITY_THRESHOLD:
                self.prosperity_streak += 1
            else:
                self.prosperity_streak = 0
            if self.prosperity_streak >= self.config.PROSPERITY_STREAK:
                self.done = True
                self.termination_reason = TERMINATION_PROSPERITY

    def _check_standard_termination(self) -> None:
        if self.shutdown_counter >= self.config.SHUTDOWN_THRESHOLD:
            self.done = True
            self.termination_reason = TERMINATION_SHUTDOWN
        elif self.treasury.is_bankrupt():
            self.done = True
            self.termination_reason = TERMINATION_BANKRUPTCY
        elif self.round >= self.config.MAX_ROUNDS:
            self.done = True
            self.termination_reason = TERMINATION_MAX_ROUNDS

    def _update_shutdown_counter(self) -> None:
        if self.last_total_allocation == 0:
            self.shutdown_counter += 1
        else:
            self.shutdown_counter = 0

    def _advance_phase(self) -> None:
        if self.done:
            return

        if self.phase == Phase.DEBATE:
            # Debate stays until force_advance_phase is called
            return

        if self.phase == Phase.PROPOSAL:
            # Only advance if all departments have either submitted or abstained
            total_active = len(self._submitted_departments) + len(self._abstained_departments)
            if total_active < len(self.sectors):
                return

        if self.phase == Phase.VOTING:
            # Only advance if all pending proposals have been voted on by everyone else
            pending = [p for p in self.proposals if p.status == PROPOSAL_STATUS_PENDING]
            if pending:
                for p in pending:
                    # Everyone except the proposer must vote
                    required_votes = len(self.sectors) - 1
                    if len(p.votes) < required_votes:
                        return
                # If we reach here, all pending proposals are fully voted.
                self._tally_votes()
            else:
                # No proposals to vote on? Advance.
                pass

        if self.phase == Phase.TERMINATION_CHECK:
            self.round += 1
            self.phase = Phase.EVENT_REVELATION
            return
        self.phase = Phase(int(self.phase) + 1)

    def force_advance_phase(self) -> None:
        """Force the phase to advance (used to end Debate)."""
        if self.done:
            return
        if self.phase == Phase.TERMINATION_CHECK:
            self.round += 1
            self.phase = Phase.EVENT_REVELATION
        else:
            self.phase = Phase(int(self.phase) + 1)

    def reopen_proposal_phase(self, rejected_departments: list[str]) -> None:
        """Rewind to Phase 3 for rejected departments only.

        Called by the environment wrapper when the retry loop is active.
        Keeps approved proposals intact, clears rejected ones, and allows
        the rejected departments to re-propose.
        """
        # Remove rejected proposals so they can be re-submitted
        self.proposals = [
            p for p in self.proposals
            if p.department not in rejected_departments
            or p.status == "approved"
        ]
        # Allow rejected departments to submit again
        for dept in rejected_departments:
            self._submitted_departments.discard(dept)
            self._abstained_departments.discard(dept)
        # Clear votes (new proposals need new votes)
        self.votes = []
        # Rewind phase
        self.phase = Phase.PROPOSAL

    def apply_fallback_allocations(self, departments: list[str]) -> None:
        """Auto-assign baseline demand for departments that exhausted retries.

        Creates approved proposals at baseline demand for each department.
        """
        for dept in departments:
            if dept in self.sectors and dept not in self._submitted_departments:
                baseline = self.sectors[dept].baseline
                self._new_proposal(
                    agent_id=dept,
                    department=dept,
                    amount=baseline,
                    justification="Fallback: baseline demand after retry exhaustion.",
                    status="approved",
                )
                self._submitted_departments.add(dept)

    def _new_proposal(
        self,
        *,
        agent_id: str,
        department: str,
        amount: float,
        justification: str = "",
        status: str = PROPOSAL_STATUS_PENDING,
        rejection_reason: str | None = None,
    ) -> Proposal:
        self._proposal_counter += 1
        proposal = Proposal(
            proposal_id=f"r{self.round}-p{self._proposal_counter}",
            agent_id=agent_id,
            department=department,
            amount=amount,
            justification=justification,
            status=status,
            rejection_reason=rejection_reason,
        )
        self.proposals.append(proposal)
        return proposal

    def _proposal_rejection_reason(self, agent_id: str, department: str, amount: Any) -> str | None:
        amount_value = self._safe_float(amount)
        if department not in self.sectors:
            return "unknown_department"
        if agent_id != department:
            return "wrong_department"
        if amount_value < 0 or math.isnan(amount_value) or math.isinf(amount_value):
            return "invalid_amount"
        if amount_value > self.treasury.balance:
            return "exceeds_treasury"
        return None

    def _proposal_by_id(self, proposal_id: str) -> Proposal | None:
        return next((proposal for proposal in self.proposals if proposal.proposal_id == proposal_id), None)

    def _result(self, info: dict[str, Any], completed_round: int | None = None) -> StepResult:
        observation = self.state()
        if completed_round is not None:
            year, quarter = self._year_quarter(completed_round)
            observation["round"] = completed_round
            observation["year"] = year
            observation["quarter"] = quarter
        return StepResult(
            observation=observation,
            reward=self.last_reward,
            done=self.done,
            info={
                **info,
                "termination_reason": self.termination_reason,
                "crisis_occurred": self.current_round_crisis,
            },
        )

    def _normalize_actions(self, action: Any) -> list[Mapping[str, Any]]:
        if action is None:
            return []
        if hasattr(action, "to_dict"):
            return [action.to_dict()]
        if isinstance(action, Mapping):
            return [action]
        if isinstance(action, Iterable) and not isinstance(action, (str, bytes)):
            normalized = []
            for item in action:
                if hasattr(item, "to_dict"):
                    normalized.append(item.to_dict())
                elif isinstance(item, Mapping):
                    normalized.append(item)
            return normalized
        return []

    def _is_allocation_mapping(self, action: Any) -> bool:
        return (
            isinstance(action, Mapping)
            and "type" not in action
            and bool(action)
            and set(action).issubset(set(self.config.SECTOR_ORDER))
        )

    def _action_type_value(self, action_type: Any) -> str:
        if isinstance(action_type, StrEnum):
            return action_type.value
        return str(action_type)

    def _vote_value(self, vote: Any) -> str | None:
        value = vote.value if isinstance(vote, StrEnum) else str(vote)
        return value if value in {choice.value for choice in VoteChoice} else None

    def _safe_float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return math.nan

    def _year_quarter(self, round_num: int) -> tuple[int, int]:
        year = (round_num - 1) // 4 + 1
        quarter = (round_num - 1) % 4 + 1
        return year, quarter
