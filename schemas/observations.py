"""Observation schema for phased multi-agent policy adapters."""

from dataclasses import dataclass, field
from typing import Any

from schemas.phases import Phase


@dataclass(frozen=True, slots=True)
class OwnDepartmentObservation:
    name: str
    allocated_budget: float | None = None
    consumption: float | None = None
    surplus: float | None = None
    efficiency_rating: float | None = None
    treasury_surplus_returned_this_round: float | None = None


@dataclass(frozen=True, slots=True)
class ProposalObservation:
    proposal_id: str
    department: str
    amount: float
    status: str = "pending"
    agent_id: str | None = None
    votes: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VoteObservation:
    proposal_id: str
    agent_id: str
    vote: str


@dataclass(frozen=True, slots=True)
class Observation:
    round: int
    phase: Phase
    treasury: float
    own_department: OwnDepartmentObservation
    event_ledger: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    proposals: tuple[ProposalObservation, ...] = field(default_factory=tuple)
    votes: tuple[VoteObservation, ...] = field(default_factory=tuple)
    debate_messages: tuple[dict[str, str], ...] = field(default_factory=tuple)
    target_proposal_id: str | None = None
    termination: dict[str, Any] = field(default_factory=dict)
