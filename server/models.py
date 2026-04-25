"""OpenEnv Pydantic models for the Nation Simulator parliamentary environment."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator
from openenv.core.env_server import Action, Observation, State


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
    treasury_surplus_returned_this_round: float | None = None
    baseline: float | None = None


# --- OpenEnv Action ---


class ParliamentaryAction(Action):
    """
    A single agent action in the parliamentary cycle.

    The `type` field determines which optional fields are required:
      - DEBATE:                 requires `message`
      - FINISH_DEBATE:          requires `reason`
      - PROPOSE_BUDGET:         requires `department`, `amount`, `justification`
      - VOTE:                   requires `proposal_id`, `vote`
    """

    agent_id: str
    type: str  # DEBATE | FINISH_DEBATE | PROPOSE_BUDGET | VOTE

    # DEBATE fields
    message: str | None = None

    # FINISH_DEBATE fields
    reason: str | None = None

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
            d["vote"] = str(self.vote) if self.vote else "ABSTAIN"
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
    year: int = 1
    quarter: int = 1
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
    target_proposal_id: str | None = None

    # Termination info
    termination: dict[str, Any] = Field(default_factory=dict)

    # Which agent should act next (set by environment)
    current_agent: str | None = None

    # Retry info
    retry_count: int = 0
    rejected_departments: list[str] = Field(default_factory=list)


# --- Legacy OpenEnv Action ---


class NationAction(Action):
    """OpenEnv action envelope for direct allocation and smoke clients."""

    bids: list[float] | None = Field(
        default=None,
        min_length=6,
        max_length=6,
        description="Legacy continuous bids from each of the 6 sectors.",
    )
    actions: dict[str, Any] | list[dict[str, Any]] | None = Field(
        default=None,
        description="One phase action or a list of phase actions.",
    )
    direct_allocations: dict[str, float] | None = Field(
        default=None,
        description="Full-round direct allocation shortcut keyed by department.",
    )

    @model_validator(mode="after")
    def require_single_action_source(self) -> "NationAction":
        sources = [
            self.bids is not None,
            self.actions is not None,
            self.direct_allocations is not None,
        ]
        if sum(sources) != 1:
            raise ValueError("Provide exactly one of bids, actions, or direct_allocations.")
        return self

    def to_core_action(self) -> Any:
        if self.direct_allocations is not None:
            return dict(self.direct_allocations)
        return self.actions


class NationObservation(Observation):
    """Serializable whole-game observation for the thin OpenEnv wrapper."""

    state: dict[str, Any] = Field(description="Public NationGame state snapshot.")
    info: dict[str, Any] = Field(default_factory=dict)


# --- OpenEnv State ---


class NationState(State):
    """Internal state for the OpenEnv environment."""

    raw_game_state: dict[str, Any] = Field(default_factory=dict)
    core_state: dict[str, Any] = Field(default_factory=dict)
