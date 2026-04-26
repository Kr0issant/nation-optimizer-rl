"""Profit-zone heuristic baseline (discretionary ask above critical)."""

from collections.abc import Iterable

from agents.rule_based.conservative import ConservativeAdapter
from agents.rule_based.discretionary import (
    discretionary_for_target_total,
    discretionary_pool,
)
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
        c = float(observation.own_department.critical)
        target_total = baseline * OPTIMAL_ZONE_MULTIPLIER
        pool = discretionary_pool(observation)
        d = discretionary_for_target_total(
            want_total=target_total, own_critical=c, pool=pool
        )
        return ProposeBudgetAction(
            type=ActionType.PROPOSE_BUDGET,
            department=observation.own_department.name,
            amount=d,
            justification="Target the profit zone above demand without entering wastage.",
        )
