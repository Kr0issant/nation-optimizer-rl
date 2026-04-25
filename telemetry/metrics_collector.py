"""Metric accumulator for seeded evaluation and rollout runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import pvariance
from typing import Any

from schemas.metrics import EpisodeMetrics


@dataclass(slots=True)
class MetricsCollector:
    total_reward: float = 0.0
    rounds_survived: int = 0
    final_treasury: float | None = None
    final_prosperity: float | None = None
    final_productivity: float | None = None
    termination_reason: str | None = None
    invalid_action_count: int = 0
    parse_error_count: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    critical_failure_count: int = 0
    bankruptcy_count: int = 0
    shutdown_count: int = 0
    debate_message_count: int = 0
    proposals_passed_count: int = 0
    _revenue_factors: list[float] = field(default_factory=list, repr=False)
    _treasury_values: list[float] = field(default_factory=list, repr=False)
    _initial_productivity: float | None = field(default=None, repr=False)
    _termination_counted: bool = field(default=False, repr=False)

    def record_step(self, reward: float, round_number: int) -> None:
        self.record_reward(reward, round_number=round_number)

    def record_reward(self, reward: float, *, round_number: int | None = None) -> None:
        self.total_reward += reward
        if round_number is not None:
            self.rounds_survived = max(self.rounds_survived, round_number)

    def record_round(self, round_number: int) -> None:
        self.rounds_survived = max(self.rounds_survived, round_number)

    def record_action_validation(
        self,
        *,
        is_valid: bool,
        parse_error: bool = False,
    ) -> None:
        if not is_valid:
            self.invalid_action_count += 1
        if parse_error:
            self.parse_error_count += 1

    def record_invalid_action(self, *, parse_error: bool = False) -> None:
        self.record_action_validation(is_valid=False, parse_error=parse_error)

    def record_llm_tokens(
        self,
        *,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
    ) -> None:
        prompt_count = prompt_tokens or 0
        completion_count = completion_tokens or 0
        self.prompt_tokens += prompt_count
        self.completion_tokens += completion_count
        if total_tokens is not None:
            self.total_tokens += total_tokens
            return
        self.total_tokens += prompt_count + completion_count

    def record_revenue_factor(self, revenue_factor: float) -> None:
        self._revenue_factors.append(revenue_factor)

    def record_treasury(self, treasury: float) -> None:
        self.final_treasury = treasury
        self._treasury_values.append(treasury)

    def record_productivity(self, productivity: float) -> None:
        if self._initial_productivity is None:
            self._initial_productivity = productivity
        self.final_productivity = productivity

    def record_debate_message(self, count: int = 1) -> None:
        self.debate_message_count += count

    def record_proposal_passed(self, count: int = 1) -> None:
        self.proposals_passed_count += count

    def record_termination(self, termination_reason: str) -> None:
        self.termination_reason = termination_reason
        if self._termination_counted:
            return

        normalized_reason = termination_reason.lower()
        if "critical" in normalized_reason:
            self.critical_failure_count += 1
        elif "bankrupt" in normalized_reason:
            self.bankruptcy_count += 1
        elif "shutdown" in normalized_reason or "governance collapse" in normalized_reason:
            self.shutdown_count += 1
        self._termination_counted = True

    def record_final_state(
        self,
        *,
        final_treasury: float | None = None,
        final_prosperity: float | None = None,
        final_productivity: float | None = None,
        termination_reason: str | None = None,
        rounds_survived: int | None = None,
    ) -> None:
        if final_treasury is not None:
            if self._treasury_values and self._treasury_values[-1] == final_treasury:
                self.final_treasury = final_treasury
            else:
                self.record_treasury(final_treasury)
        self.final_prosperity = final_prosperity
        if final_productivity is not None:
            self.final_productivity = final_productivity
        if termination_reason is not None:
            self.record_termination(termination_reason)
        if rounds_survived is not None:
            self.rounds_survived = max(self.rounds_survived, rounds_survived)

    def build_summary(self, episode_id: str, **overrides: Any) -> EpisodeMetrics:
        productivity_growth = None
        if self._initial_productivity is not None and self.final_productivity is not None:
            productivity_growth = self.final_productivity - self._initial_productivity

        values = {
            "episode_id": episode_id,
            "rounds_survived": self.rounds_survived,
            "total_reward": self.total_reward,
            "final_prosperity": self.final_prosperity,
            "final_treasury": self.final_treasury,
            "final_productivity": self.final_productivity,
            "termination_reason": self.termination_reason,
            "invalid_action_count": self.invalid_action_count,
            "parse_error_count": self.parse_error_count,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "critical_failure_count": self.critical_failure_count,
            "bankruptcy_count": self.bankruptcy_count,
            "shutdown_count": self.shutdown_count,
            "average_revenue_factor": _mean(self._revenue_factors),
            "treasury_stability": _variance(self._treasury_values),
            "productivity_growth": productivity_growth,
            "debate_message_count": self.debate_message_count,
            "proposals_passed_count": self.proposals_passed_count,
        }
        values.update(overrides)
        return EpisodeMetrics(**values)


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _variance(values: list[float]) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return 0.0
    return pvariance(values)
