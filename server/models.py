"""OpenEnv Pydantic models for the Nation Simulator parliamentary environment."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field
from openenv_core import Observation, Action, State


# --- Supporting Models ---


class EventModel(BaseModel):
    """An event revealed during Phase 1."""

    name: str
    severity: int
    category: str
    narrative: str
    affected_departments: list[str] = Field(default_factory=list)
    round: int | None = None
    cost: float | None = None


class NationAction(BaseModel):
    """The continuous action space for the 6 sectors (legacy OpenEnv API)."""

    bids: list[float] = Field(
        ...,
        min_length=6,
        max_length=6,
        description="Continuous bids from each of the 6 sectors.",
    )


class ProposalModel(BaseModel):
    """A budget proposal submitted during Phase 3."""

    proposal_id: str
    agent_id: str
    department: str
    amount: float
    justification: str = ""
    status: str = "pending"
    votes: dict[str, str] = Field(default_factory=dict)
    rejection_reason: str | None = None


class VoteModel(BaseModel):
    """A single vote cast during Phase 4."""

    proposal_id: str
    agent_id: str
    vote: str  # YES / NO / ABSTAIN


class OwnDepartmentModel(BaseModel):
    """Private observation for a specific department's minister."""

    name: str
    allocated_budget: float | None = None
    consumption: float | None = None
    surplus: float | None = None
    efficiency_rating: float | None = None
    baseline: float | None = None


# --- OpenEnv Action ---


class ParliamentaryAction(Action):
    """
    A single agent action in the parliamentary cycle.

    The `type` field determines which optional fields are required:
      - DEBATE:                 requires `message`
      - PROPOSE_BUDGET:         requires `department`, `amount`, `justification`
      - VOTE:                   requires `proposal_id`, `vote`
      - ABSTAIN_FROM_PROPOSAL:  no extra fields needed
    """

    agent_id: str
    type: str  # DEBATE | PROPOSE_BUDGET | VOTE | ABSTAIN_FROM_PROPOSAL

    # DEBATE fields
    message: str | None = None

    # PROPOSE_BUDGET fields
    department: str | None = None
    amount: float | None = None
    justification: str | None = None

    # VOTE fields
    proposal_id: str | None = None
    vote: str | None = None  # YES / NO / ABSTAIN

    def to_engine_dict(self) -> dict[str, Any]:
        """Convert to the dict format expected by core/game.py step()."""
        d: dict[str, Any] = {"type": self.type, "agent_id": self.agent_id}
        if self.type == "DEBATE":
            d["message"] = self.message or ""
        elif self.type == "PROPOSE_BUDGET":
            d["department"] = self.department or ""
            d["amount"] = self.amount if self.amount is not None else 0.0
            d["justification"] = self.justification or ""
        elif self.type == "VOTE":
            d["proposal_id"] = self.proposal_id or ""
            d["vote"] = self.vote or "ABSTAIN"
        elif self.type == "ABSTAIN_FROM_PROPOSAL":
            d["department"] = self.department or self.agent_id
        return d


# --- OpenEnv Observation ---


class ParliamentaryObservation(Observation):
    """
    Full spec-compliant observation per 08_OBSERVATION_SPACE.md.

    Includes all public information plus private `own_department` data
    for the specific agent receiving the observation.
    """

    round: int = 0
    phase: int = 1
    phase_name: str = "EVENT_REVELATION"
    treasury: float = 0.0
    population: int = 0
    productivity: float = 1.0

    # Public information
    event_ledger: list[dict[str, Any]] = Field(default_factory=list)
    current_events: list[EventModel] = Field(default_factory=list)
    proposals: list[ProposalModel] = Field(default_factory=list)
    votes: list[VoteModel] = Field(default_factory=list)
    debate_messages: list[dict[str, str]] = Field(default_factory=list)

    # Private to the observing agent
    own_department: OwnDepartmentModel | None = None

    # Phase-gated action mask
    valid_actions: list[str] = Field(default_factory=list)

    # Termination info
    termination: dict[str, Any] = Field(default_factory=dict)

    # Which agent should act next (set by environment)
    current_agent: str | None = None

    # Retry info
    retry_count: int = 0
    rejected_departments: list[str] = Field(default_factory=list)


# --- OpenEnv State ---


class NationState(State):
    """Internal state for the OpenEnv environment."""

    raw_game_state: dict[str, Any] = Field(default_factory=dict)
