"""OpenEnv parliamentary environment for the Nation Simulator."""

from __future__ import annotations

from typing import Any, Optional

from openenv_core import Environment

from core.game import NationGame
from schemas.phases import Phase, valid_action_types_for_phase
from server.models import (
    ParliamentaryAction,
    ParliamentaryObservation,
    NationState,
    EventModel,
    ProposalModel,
    VoteModel,
    OwnDepartmentModel,
)

import numpy as np

# Maximum retry attempts for rejected proposals before fallback
MAX_PROPOSAL_RETRIES = 2


class NationEnvironment(Environment):
    """
    OpenEnv wrapper exposing the full 9-phase parliamentary cycle.

    Each call to step() processes ONE agent action in the current phase.
    System-only phases (5-9) are auto-advanced after all agent actions
    in a phase are complete.

    Retry loop: after voting, if any proposals were rejected, the environment
    loops back to Phase 3 for rejected departments (up to MAX_PROPOSAL_RETRIES
    times). After retries are exhausted, rejected departments receive baseline
    demand as a fallback.
    """

    def __init__(self, seed: int | None = None):
        super().__init__()
        self.game = NationGame(seed=seed)
        self.departments = list(self.game.config.SECTOR_ORDER)
        self._retry_count = 0
        self._round_reward = 0.0

    @property
    def state(self) -> NationState:
        """Returns the current internal state of the environment."""
        return NationState(
            step_count=self.game.round,
            raw_game_state=self.game.state(),
        )

    def reset(
        self, seed: Optional[int] = None, **kwargs
    ) -> tuple[ParliamentaryObservation, dict]:
        """
        Reset the environment. Phase 1 (event revelation) runs automatically.
        Returns observation ready for Phase 2 (debate).
        """
        super().reset(seed=seed)
        if seed is not None:
            self.game = NationGame(seed=seed)
        else:
            self.game.reset()

        self._retry_count = 0
        self._round_reward = 0.0

        # Phase 1 already ran inside game.reset() → _start_round()
        # Engine starts in Phase 1. We need to advance to Phase 2 for debate.
        self.game.force_advance_phase()

        obs = self._build_observation(agent_id=self.departments[0])
        return obs, {}

    def step(
        self, action: ParliamentaryAction
    ) -> tuple[ParliamentaryObservation, float, bool, bool, dict]:
        """
        Process one agent action in the current phase.
        """
        # Special case: an empty DEBATE message can be used to signal "pass/finish"
        if action.type == "DEBATE" and not (action.message or "").strip():
            self.game.force_advance_phase()
            next_agent = self._determine_next_agent()
            obs = self._build_observation(agent_id=next_agent)
            return obs, 0.0, False, False, {"action": "debate_pass"}

        # Convert to engine dict and step
        action_dict = action.to_engine_dict()
        result = self.game.step(action_dict)

        # Check if the episode ended during this step
        if self.game.done:
            self._round_reward = result.reward.total
            obs = self._build_observation(agent_id=action.agent_id)
            return obs, self._round_reward, True, False, self._build_info(result)

        # Handle phase transitions
        if self.game.phase == Phase.BUDGET_EXECUTION:
            rejected = self._get_rejected_departments()
            if rejected and self._retry_count < MAX_PROPOSAL_RETRIES:
                self._retry_count += 1
                self.game.reopen_proposal_phase(rejected)
                obs = self._build_observation(
                    agent_id=rejected[0],
                    rejected_departments=rejected,
                )
                return (
                    obs,
                    0.0,
                    False,
                    False,
                    {
                        "retry": True,
                        "retry_count": self._retry_count,
                        "rejected_departments": rejected,
                    },
                )
            elif rejected and self._retry_count >= MAX_PROPOSAL_RETRIES:
                self.game.apply_fallback_allocations(rejected)

            return self._run_system_phases(action.agent_id)

        # Still in an agent phase — return observation for next action
        next_agent = self._determine_next_agent()
        obs = self._build_observation(agent_id=next_agent)
        return obs, 0.0, False, False, self._build_info(result)

    def _run_system_phases(
        self, last_agent_id: str
    ) -> tuple[ParliamentaryObservation, float, bool, bool, dict]:
        """
        Auto-advance through system phases 5-9.
        Returns the final observation + reward for this round.
        """
        # Step through system phases until we reach next round's agent phase or done
        result = None
        while not self.game.done and self.game.phase in (
            Phase.BUDGET_EXECUTION,
            Phase.CONSUMPTION_AND_EVENT_IMPACT,
            Phase.REVENUE_CALCULATION,
            Phase.SURPLUS_ROLLOVER,
            Phase.TERMINATION_CHECK,
        ):
            result = self.game.step(None)

        # Capture the round reward if available
        if result:
            self._round_reward = result.reward.total

        if self.game.done:
            obs = self._build_observation(agent_id=last_agent_id)
            return obs, self._round_reward, True, False, self._build_info(result)

        # New round started — Phase 1 runs automatically in game.step
        # Advance to Phase 2 for agents
        if self.game.phase == Phase.EVENT_REVELATION:
            self.game.phase = Phase.DEBATE

        self._retry_count = 0
        next_agent = self._determine_next_agent()
        obs = self._build_observation(agent_id=next_agent)
        return obs, self._round_reward, False, False, self._build_info(result)

    def _get_rejected_departments(self) -> list[str]:
        """Return departments whose proposals were rejected in voting."""
        rejected = []
        proposed_depts = set()
        for p in self.game.proposals:
            proposed_depts.add(p.department)
            if p.status == "rejected" or p.status == "rejected_invalid":
                rejected.append(p.department)

        # Also include departments that abstained or never proposed
        for dept in self.departments:
            if (
                dept not in proposed_depts
                and dept not in self.game._abstained_departments
            ):
                # Department never proposed — they need a proposal
                if dept not in rejected:
                    rejected.append(dept)

        return rejected

    def _determine_next_agent(self) -> str:
        """Determine which agent should act next based on current phase."""
        phase = self.game.phase

        if phase == Phase.DEBATE:
            # During debate, any agent can speak; return first department
            return self.departments[0]

        if phase == Phase.PROPOSAL:
            # Return first department that hasn't submitted yet
            for dept in self._get_proposal_order():
                if (
                    dept not in self.game._submitted_departments
                    and dept not in self.game._abstained_departments
                ):
                    return dept
            return self.departments[0]

        if phase == Phase.VOTING:
            # Return first agent who has a pending vote on the current proposal
            pending = [p for p in self.game.proposals if p.status == "pending"]
            for target in pending:
                # Everyone except the proposer must vote
                required_votes = len(self.departments) - 1
                if len(target.votes) < required_votes:
                    for dept in self.departments:
                        if dept == target.agent_id or dept == target.department:
                            continue
                        if dept not in target.votes:
                            return dept
            return self.departments[0]

        return self.departments[0]

    def _get_proposal_order(self) -> list[str]:
        """Get the rotating proposal order for the current round."""
        n = len(self.departments)
        start_idx = (self.game.round - 1) % n
        return self.departments[start_idx:] + self.departments[:start_idx]

    def _build_observation(
        self,
        agent_id: str,
        rejected_departments: list[str] | None = None,
    ) -> ParliamentaryObservation:
        """Build a spec-compliant observation for a specific agent."""
        gs = self.game.state()

        # Current events
        current_events = [
            EventModel(
                name=e.get("name", ""),
                severity=e.get("severity", 0),
                category=e.get("category", ""),
                narrative=e.get("narrative", ""),
                affected_departments=e.get("affected_departments", []),
                round=e.get("round"),
                cost=e.get("cost"),
            )
            for e in gs.get("current_events", [])
        ]

        # Proposals
        proposals = [
            ProposalModel(
                proposal_id=p.get("proposal_id", ""),
                agent_id=p.get("agent_id", ""),
                department=p.get("department", ""),
                amount=p.get("amount", 0.0),
                justification=p.get("justification", ""),
                status=p.get("status", "pending"),
                votes=p.get("votes", {}),
                rejection_reason=p.get("rejection_reason"),
            )
            for p in gs.get("proposals", [])
        ]

        # Votes
        votes = [
            VoteModel(
                proposal_id=v.get("proposal_id", ""),
                agent_id=v.get("agent_id", ""),
                vote=v.get("vote", ""),
            )
            for v in gs.get("votes", [])
        ]

        # Own department private info
        own_dept = None
        sectors = gs.get("sectors", {})
        if agent_id in sectors:
            s = sectors[agent_id]
            own_dept = OwnDepartmentModel(
                name=agent_id,
                allocated_budget=s.get("allocation"),
                consumption=s.get("consumption"),
                surplus=s.get("surplus"),
                efficiency_rating=s.get("revenue_factor"),
                baseline=s.get("baseline"),
            )

        # Valid actions for current phase
        phase = gs.get("phase")
        if phase is not None:
            valid = list(valid_action_types_for_phase(phase))
        else:
            valid = []

        return ParliamentaryObservation(
            round=gs.get("round", 0),
            phase=int(gs.get("phase", 1)),
            phase_name=gs.get("phase_name", ""),
            treasury=gs.get("treasury", 0.0),
            population=gs.get("population", 0),
            productivity=gs.get("productivity", 1.0),
            event_ledger=gs.get("event_ledger", []),
            current_events=current_events,
            proposals=proposals,
            votes=votes,
            debate_messages=gs.get("debate_messages", []),
            own_department=own_dept,
            valid_actions=valid,
            termination=gs.get("termination", {}),
            current_agent=agent_id,
            retry_count=self._retry_count,
            rejected_departments=rejected_departments or [],
            # OpenEnv base fields
            reward=0.0,
            done=self.game.done,
        )

    def _build_info(self, result: Any) -> dict[str, Any]:
        """Build the info dict from a StepResult."""
        return {
            "round": result.round_num,
            "termination_reason": result.termination_reason,
            "retry_count": self._retry_count,
        }
