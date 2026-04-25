"""Profit-zone heuristic baseline."""

from collections.abc import Iterable

from agents.rule_based.conservative import ConservativeAdapter
from schemas.actions import Action, ActionType, ProposeBudgetAction
from schemas.departments import BASELINES_BY_DEPARTMENT
from schemas.observations import Observation

OPTIMAL_ZONE_MULTIPLIER = 1.3


class OptimalZoneAdapter(ConservativeAdapter):
    def act(
        self,
        observation: Observation,
        valid_actions: Iterable[str],
        agent_id: str,
    ) -> Action:
        valid_action_set = set(valid_actions)
        if ActionType.PROPOSE_BUDGET.value not in valid_action_set:
            return super().act(observation, valid_actions, agent_id)

        baseline = BASELINES_BY_DEPARTMENT[observation.own_department.name]
        target_amount = baseline * OPTIMAL_ZONE_MULTIPLIER
        return ProposeBudgetAction(
            type=ActionType.PROPOSE_BUDGET,
            department=observation.own_department.name,
            amount=min(target_amount, observation.treasury),
            justification="Target the profit zone above demand without entering wastage.",
        )
