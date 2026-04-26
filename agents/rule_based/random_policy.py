"""Random baseline: sample uniformly from legal structured actions."""

from __future__ import annotations

import random
from collections.abc import Callable, Iterable

from agents.base import PolicyAdapter
from agents.rule_based.discretionary import discretionary_pool
from agents.rule_based.voting import is_vote_target
from schemas.actions import (
    Action,
    ActionType,
    DebateAction,
    ProposeBudgetAction,
    VoteAction,
    VoteChoice,
)
from schemas.observations import Observation, ProposalObservation


class RandomAdapter(PolicyAdapter):
    def __init__(self, seed: int | None = None, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random(seed)

    def act(
        self,
        observation: Observation,
        valid_actions: Iterable[str],
        agent_id: str,
    ) -> Action:
        candidates = self._candidate_actions(observation, set(valid_actions), agent_id)
        if not candidates:
            return DebateAction(
                type=ActionType.DEBATE,
                message=f"{agent_id} has no valid structured actions; sending a minimal debate message.",
            )
        return self.rng.choice(candidates)()

    def _candidate_actions(
        self,
        observation: Observation,
        valid_actions: set[str],
        agent_id: str,
    ) -> list[Callable[[], Action]]:
        candidates: list[Callable[[], Action]] = []

        if ActionType.PROPOSE_BUDGET.value in valid_actions:
            candidates.append(lambda: self._proposal_action(observation))

        if ActionType.VOTE.value in valid_actions:
            candidates.extend(
                self._vote_action(proposal, vote)
                for proposal in observation.proposals
                if is_vote_target(proposal, agent_id)
                for vote in VoteChoice
            )

        if ActionType.DEBATE.value in valid_actions:
            candidates.append(
                lambda: DebateAction(
                    type=ActionType.DEBATE,
                    message=f"{agent_id} shares a random priority signal.",
                )
            )

        return candidates

    def _proposal_action(self, observation: Observation) -> ProposeBudgetAction:
        pool = discretionary_pool(observation)
        hi = max(pool, 0.0)
        return ProposeBudgetAction(
            type=ActionType.PROPOSE_BUDGET,
            department=observation.own_department.name,
            amount=self.rng.uniform(0.0, hi),
            justification="Random legal discretionary amount sampled from the available pool.",
        )

    @staticmethod
    def _vote_action(proposal: ProposalObservation, vote: VoteChoice) -> Callable[[], VoteAction]:
        proposal_id = proposal.proposal_id
        return lambda: VoteAction(
            type=ActionType.VOTE,
            proposal_id=proposal_id,
            vote=vote,
        )
