"""Conservative baseline: request the department baseline demand."""

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
from schemas.departments import BASELINES_BY_DEPARTMENT
from schemas.observations import Observation


class ConservativeAdapter(PolicyAdapter):
    def act(
        self,
        observation: Observation,
        valid_actions: Iterable[str],
        agent_id: str,
    ) -> Action:
        valid_action_set = set(valid_actions)
        if ActionType.PROPOSE_BUDGET.value in valid_action_set:
            baseline = BASELINES_BY_DEPARTMENT[observation.own_department.name]
            return ProposeBudgetAction(
                type=ActionType.PROPOSE_BUDGET,
                department=observation.own_department.name,
                amount=min(baseline, observation.treasury),
                justification="Request baseline demand to avoid underfunding.",
            )

        other_pending_proposals = [
            proposal
            for proposal in observation.proposals
            if proposal.department != agent_id and proposal.status == "pending"
        ]
        if ActionType.VOTE.value in valid_action_set and other_pending_proposals:
            return VoteAction(
                type=ActionType.VOTE,
                proposal_id=other_pending_proposals[0].proposal_id,
                vote=VoteChoice.YES,
            )

        if ActionType.DEBATE.value in valid_action_set:
            return DebateAction(
                type=ActionType.DEBATE,
                message=f"{agent_id} recommends baseline-demand funding.",
            )

        return AbstainProposalAction(type=ActionType.ABSTAIN_FROM_PROPOSAL)
