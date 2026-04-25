"""Greedy baseline: each minister maximizes its own departmental request."""

from collections.abc import Iterable

from agents.base import PolicyAdapter
from agents.rule_based.voting import first_vote_target
from schemas.actions import (
    AbstainProposalAction,
    Action,
    ActionType,
    DebateAction,
    ProposeBudgetAction,
    VoteAction,
    VoteChoice,
)
from schemas.observations import Observation


class GreedyAdapter(PolicyAdapter):
    def act(
        self,
        observation: Observation,
        valid_actions: Iterable[str],
        agent_id: str,
    ) -> Action:
        valid_action_set = set(valid_actions)
        if ActionType.PROPOSE_BUDGET.value in valid_action_set:
            return ProposeBudgetAction(
                type=ActionType.PROPOSE_BUDGET,
                department=observation.own_department.name,
                amount=observation.treasury,
                justification="Maximize this department's immediate allocation.",
            )

        vote_target = first_vote_target(observation.proposals, agent_id)
        if ActionType.VOTE.value in valid_action_set and vote_target is not None:
            return VoteAction(
                type=ActionType.VOTE,
                proposal_id=vote_target.proposal_id,
                vote=VoteChoice.YES,
            )

        if ActionType.DEBATE.value in valid_action_set:
            return DebateAction(
                type=ActionType.DEBATE,
                message=f"{agent_id} requests priority for {observation.own_department.name}.",
            )

        return AbstainProposalAction(type=ActionType.ABSTAIN_FROM_PROPOSAL)
