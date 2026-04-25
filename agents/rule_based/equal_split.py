"""Equal-split baseline: request an even share of the visible treasury."""

from collections.abc import Iterable

from agents.base import PolicyAdapter
from schemas.actions import (
    AbstainProposalAction,
    Action,
    ActionType,
    DebateAction,
    ProposeBudgetAction,
    VoteAction,
    VoteChoice,
)
from schemas.departments import DEFAULT_DEPARTMENT_NAMES
from schemas.observations import Observation


class EqualSplitAdapter(PolicyAdapter):
    def __init__(self, department_count: int = len(DEFAULT_DEPARTMENT_NAMES)) -> None:
        if department_count <= 0:
            raise ValueError("department_count must be positive.")
        self.department_count = department_count

    def act(
        self,
        observation: Observation,
        valid_actions: Iterable[str],
        agent_id: str,
    ) -> Action:
        valid_action_set = set(valid_actions)
        if ActionType.PROPOSE_BUDGET.value in valid_action_set:
            share = observation.treasury / self.department_count
            return ProposeBudgetAction(
                type=ActionType.PROPOSE_BUDGET,
                department=observation.own_department.name,
                amount=share,
                justification="Request an equal share of the visible treasury.",
            )

        if ActionType.VOTE.value in valid_action_set and observation.proposals:
            return VoteAction(
                type=ActionType.VOTE,
                proposal_id=observation.proposals[0].proposal_id,
                vote=VoteChoice.YES,
            )

        if ActionType.DEBATE.value in valid_action_set:
            return DebateAction(
                type=ActionType.DEBATE,
                message=f"{agent_id} supports equal treasury distribution.",
            )

        return AbstainProposalAction(type=ActionType.ABSTAIN_FROM_PROPOSAL)
