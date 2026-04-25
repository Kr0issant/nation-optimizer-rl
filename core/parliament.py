"""Parliamentary action collection and budget resolution.

This module is a narrow adapter between phased parliamentary actions and the
round-level allocation mapping accepted by :class:`core.game.NationGame`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

from schemas.actions import ActionType, VoteChoice
from schemas.phases import Phase


PROPOSAL_STATUS_APPROVED = "approved"
PROPOSAL_STATUS_REJECTED_ALL_ABSTAIN = "rejected_all_abstain"
PROPOSAL_STATUS_REJECTED_TIE = "rejected_tie"
PROPOSAL_STATUS_REJECTED_MAJORITY = "rejected_majority"
PROPOSAL_STATUS_REJECTED_OVER_BUDGET = "rejected_exceeds_remaining_treasury"


@dataclass(frozen=True, slots=True)
class Proposal:
    """Public budget request submitted by a minister for their department."""

    proposal_id: str
    agent_id: str
    department: str
    amount: float
    justification: str = ""
    submitted_order: int = 0


@dataclass(frozen=True, slots=True)
class VoteRecord:
    """Public vote cast by one agent on one proposal."""

    proposal_id: str
    agent_id: str
    vote: VoteChoice
    cast_order: int = 0


@dataclass(frozen=True, slots=True)
class DebateMessage:
    """Public debate message visible to all agents."""

    agent_id: str
    message: str
    submitted_order: int = 0


@dataclass(frozen=True, slots=True)
class ProposalAbstention:
    """Explicit record that a minister skipped their proposal turn."""

    agent_id: str
    department: str
    submitted_order: int = 0


@dataclass(frozen=True, slots=True)
class ResolutionResult:
    """Resolved parliamentary round output for the core game engine."""

    allocations: dict[str, float]
    approved_proposal_ids: list[str]
    rejected_proposal_ids: list[str]
    proposal_outcomes: dict[str, str]
    vote_counts: dict[str, dict[str, int]]
    remaining_treasury: float
    proposals: list[Proposal]
    votes: list[VoteRecord]
    debate_messages: list[DebateMessage]
    proposal_abstentions: list[ProposalAbstention]


@dataclass(slots=True)
class ParliamentRoundState:
    """Collects debate, proposal, and vote actions for a single round."""

    round_number: int
    treasury_at_start: float
    agent_departments: Mapping[str, str]
    proposals: list[Proposal] = field(default_factory=list)
    votes: list[VoteRecord] = field(default_factory=list)
    debate_messages: list[DebateMessage] = field(default_factory=list)
    proposal_abstentions: list[ProposalAbstention] = field(default_factory=list)
    _proposal_counter: int = 0
    _vote_counter: int = 0
    _debate_counter: int = 0
    _abstention_counter: int = 0
    _proposing_agents: set[str] = field(default_factory=set)
    _abstaining_agents: set[str] = field(default_factory=set)
    _votes_by_proposal_agent: set[tuple[str, str]] = field(default_factory=set)

    def collect_action(
        self,
        phase: Phase,
        action: Any,
    ) -> Proposal | VoteRecord | DebateMessage | ProposalAbstention | None:
        """Collect one structured action if it belongs to the supplied phase."""

        data = _action_to_mapping(action)
        action_type = _enum_value(data.get("type"))

        if Phase(phase) == Phase.DEBATE and action_type == ActionType.DEBATE.value:
            return self.submit_debate(
                agent_id=str(data.get("agent_id") or data.get("agent") or "anonymous"),
                message=str(data.get("message", "")),
            )
        if Phase(phase) == Phase.PROPOSAL and action_type == ActionType.PROPOSE_BUDGET.value:
            return self.submit_proposal(
                agent_id=str(data.get("agent_id") or data.get("agent") or ""),
                department=str(data.get("department", "")),
                amount=data.get("amount"),
                justification=str(data.get("justification", "")),
            )
        if Phase(phase) == Phase.PROPOSAL and action_type == ActionType.ABSTAIN_FROM_PROPOSAL.value:
            return self.submit_abstention(
                agent_id=str(data.get("agent_id") or data.get("agent") or ""),
            )
        if Phase(phase) == Phase.VOTING and action_type == ActionType.VOTE.value:
            return self.submit_vote(
                agent_id=str(data.get("agent_id") or data.get("agent") or ""),
                proposal_id=str(data.get("proposal_id", "")),
                vote=data.get("vote"),
            )
        return None

    def submit_debate(self, agent_id: str, message: str) -> DebateMessage:
        """Record a public debate message."""

        self._debate_counter += 1
        debate_message = DebateMessage(
            agent_id=agent_id,
            message=message,
            submitted_order=self._debate_counter,
        )
        self.debate_messages.append(debate_message)
        return debate_message

    def submit_abstention(self, agent_id: str) -> ProposalAbstention:
        """Record that an agent explicitly skipped their proposal turn."""

        department = self.agent_departments.get(agent_id)
        if department is None:
            raise ValueError("unknown_agent")
        if agent_id in self._proposing_agents or agent_id in self._abstaining_agents:
            raise ValueError("duplicate_abstention")

        self._abstention_counter += 1
        abstention = ProposalAbstention(
            agent_id=agent_id,
            department=department,
            submitted_order=self._abstention_counter,
        )
        self.proposal_abstentions.append(abstention)
        self._abstaining_agents.add(agent_id)
        return abstention

    def submit_proposal(
        self,
        agent_id: str,
        department: str,
        amount: Any,
        justification: str = "",
    ) -> Proposal:
        """Validate and record a proposal for the agent's assigned department."""

        if agent_id in self._proposing_agents or agent_id in self._abstaining_agents:
            raise ValueError("duplicate_proposal")
        if self.agent_departments.get(agent_id) != department:
            raise ValueError("wrong_department")

        amount_value = _validate_amount(amount)
        if amount_value > self.treasury_at_start:
            raise ValueError("exceeds_treasury")

        self._proposal_counter += 1
        proposal = Proposal(
            proposal_id=f"r{self.round_number}-p{self._proposal_counter}",
            agent_id=agent_id,
            department=department,
            amount=amount_value,
            justification=justification,
            submitted_order=self._proposal_counter,
        )
        self.proposals.append(proposal)
        self._proposing_agents.add(agent_id)
        return proposal

    def submit_vote(self, agent_id: str, proposal_id: str, vote: Any) -> VoteRecord:
        """Validate and record a public vote on a proposal."""

        proposal = self._proposal_by_id(proposal_id)
        if proposal is None:
            raise ValueError("proposal_not_found")
        if agent_id not in self.agent_departments:
            raise ValueError("unknown_agent")
        if agent_id == proposal.agent_id:
            raise ValueError("self_vote")

        vote_key = (proposal_id, agent_id)
        if vote_key in self._votes_by_proposal_agent:
            raise ValueError("duplicate_vote")

        vote_choice = _validate_vote(vote)
        self._vote_counter += 1
        vote_record = VoteRecord(
            proposal_id=proposal_id,
            agent_id=agent_id,
            vote=vote_choice,
            cast_order=self._vote_counter,
        )
        self.votes.append(vote_record)
        self._votes_by_proposal_agent.add(vote_key)
        return vote_record

    def resolve(self) -> ResolutionResult:
        """Resolve proposal outcomes into a ``{department: allocation}`` mapping."""

        allocations = {department: 0.0 for department in self.agent_departments.values()}
        proposal_outcomes: dict[str, str] = {}
        vote_counts: dict[str, dict[str, int]] = {}
        approved_proposal_ids: list[str] = []
        rejected_proposal_ids: list[str] = []
        remaining_treasury = float(self.treasury_at_start)

        for proposal in self.proposals:
            counts = self._vote_counts_for(proposal.proposal_id)
            vote_counts[proposal.proposal_id] = counts
            outcome = _majority_outcome(counts)

            if outcome == PROPOSAL_STATUS_APPROVED:
                if proposal.amount <= remaining_treasury:
                    allocations[proposal.department] = allocations.get(proposal.department, 0.0) + proposal.amount
                    remaining_treasury -= proposal.amount
                    approved_proposal_ids.append(proposal.proposal_id)
                else:
                    outcome = PROPOSAL_STATUS_REJECTED_OVER_BUDGET
                    rejected_proposal_ids.append(proposal.proposal_id)
            else:
                rejected_proposal_ids.append(proposal.proposal_id)

            proposal_outcomes[proposal.proposal_id] = outcome

        return ResolutionResult(
            allocations=allocations,
            approved_proposal_ids=approved_proposal_ids,
            rejected_proposal_ids=rejected_proposal_ids,
            proposal_outcomes=proposal_outcomes,
            vote_counts=vote_counts,
            remaining_treasury=remaining_treasury,
            proposals=list(self.proposals),
            votes=list(self.votes),
            debate_messages=list(self.debate_messages),
            proposal_abstentions=list(self.proposal_abstentions),
        )

    def _proposal_by_id(self, proposal_id: str) -> Proposal | None:
        return next((proposal for proposal in self.proposals if proposal.proposal_id == proposal_id), None)

    def _vote_counts_for(self, proposal_id: str) -> dict[str, int]:
        counts = {choice.value: 0 for choice in VoteChoice}
        for vote in self.votes:
            if vote.proposal_id == proposal_id:
                counts[vote.vote.value] += 1
        return counts


def _majority_outcome(counts: Mapping[str, int]) -> str:
    yes_votes = counts[VoteChoice.YES.value]
    no_votes = counts[VoteChoice.NO.value]
    non_abstaining_votes = yes_votes + no_votes

    if non_abstaining_votes == 0:
        return PROPOSAL_STATUS_REJECTED_ALL_ABSTAIN
    if yes_votes == no_votes:
        return PROPOSAL_STATUS_REJECTED_TIE
    if yes_votes > non_abstaining_votes / 2:
        return PROPOSAL_STATUS_APPROVED
    return PROPOSAL_STATUS_REJECTED_MAJORITY


def _validate_amount(amount: Any) -> float:
    if isinstance(amount, bool):
        raise ValueError("invalid_amount")
    try:
        amount_value = float(amount)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_amount") from exc
    if amount_value < 0 or math.isnan(amount_value) or math.isinf(amount_value):
        raise ValueError("invalid_amount")
    return amount_value


def _validate_vote(vote: Any) -> VoteChoice:
    vote_value = _enum_value(vote)
    try:
        return VoteChoice(vote_value)
    except ValueError as exc:
        raise ValueError("invalid_vote") from exc


def _action_to_mapping(action: Any) -> Mapping[str, Any]:
    if hasattr(action, "to_dict"):
        return action.to_dict()
    if isinstance(action, Mapping):
        return action
    raise ValueError("invalid_action")


def _enum_value(value: Any) -> str:
    if isinstance(value, StrEnum):
        return value.value
    return str(value)
