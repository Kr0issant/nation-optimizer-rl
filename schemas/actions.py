"""Structured action schema shared by agents and environment wrappers."""

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, Literal, TypeAlias


class ActionType(StrEnum):
    DEBATE = "DEBATE"
    PROPOSE_BUDGET = "PROPOSE_BUDGET"
    VOTE = "VOTE"
    ABSTAIN_FROM_PROPOSAL = "ABSTAIN_FROM_PROPOSAL"
    FINISH_DEBATE = "FINISH_DEBATE"


class VoteChoice(StrEnum):
    YES = "YES"
    NO = "NO"
    ABSTAIN = "ABSTAIN"


@dataclass(frozen=True, slots=True)
class DebateAction:
    type: Literal[ActionType.DEBATE]
    message: str

    def to_dict(self) -> dict[str, Any]:
        return _enum_safe_asdict(self)


@dataclass(frozen=True, slots=True)
class ProposeBudgetAction:
    type: Literal[ActionType.PROPOSE_BUDGET]
    department: str
    amount: float
    justification: str

    def to_dict(self) -> dict[str, Any]:
        return _enum_safe_asdict(self)


@dataclass(frozen=True, slots=True)
class VoteAction:
    type: Literal[ActionType.VOTE]
    proposal_id: str
    vote: VoteChoice

    def to_dict(self) -> dict[str, Any]:
        return _enum_safe_asdict(self)


@dataclass(frozen=True, slots=True)
class AbstainProposalAction:
    type: Literal[ActionType.ABSTAIN_FROM_PROPOSAL]

    def to_dict(self) -> dict[str, Any]:
        return _enum_safe_asdict(self)


@dataclass(frozen=True, slots=True)
class FinishDebateAction:
    type: Literal[ActionType.FINISH_DEBATE]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return _enum_safe_asdict(self)


Action: TypeAlias = (
    DebateAction | ProposeBudgetAction | VoteAction | AbstainProposalAction | FinishDebateAction
)


def _enum_safe_asdict(action: Action) -> dict[str, Any]:
    data = asdict(action)
    return {
        key: value.value if isinstance(value, StrEnum) else value
        for key, value in data.items()
    }
