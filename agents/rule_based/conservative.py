"""Conservative baseline: request up to baseline demand (discretionary)."""

from collections.abc import Iterable

from agents.base import PolicyAdapter
from agents.rule_based.discretionary import (
    discretionary_for_target_total,
    discretionary_pool,
)
from agents.rule_based.voting import first_vote_target
from schemas.actions import (
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
            c = float(observation.own_department.critical)
            dem = float(observation.own_department.demand) if observation.own_department.demand else 0.0
            want_total = min(baseline, dem) if dem else baseline
            pool = discretionary_pool(observation)
            d = discretionary_for_target_total(
                want_total=want_total, own_critical=c, pool=pool
            )
            return ProposeBudgetAction(
                type=ActionType.PROPOSE_BUDGET,
                department=observation.own_department.name,
                amount=d,
                justification="Request baseline demand to avoid underfunding.",
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
                message=f"{agent_id} recommends baseline-demand funding.",
            )

        return DebateAction(
            type=ActionType.DEBATE,
            message=f"{agent_id} has no additional structured action in this sub-phase.",
        )
