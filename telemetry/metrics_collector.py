"""Metric accumulator for seeded evaluation and rollout runs."""

from __future__ import annotations

from dataclasses import dataclass
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
        self.total_tokens += total_tokens if total_tokens is not None else (
            prompt_count + completion_count
        )

    def record_final_state(
        self,
        *,
        final_treasury: float | None = None,
        final_prosperity: float | None = None,
        final_productivity: float | None = None,
        termination_reason: str | None = None,
        rounds_survived: int | None = None,
    ) -> None:
        self.final_treasury = final_treasury
        self.final_prosperity = final_prosperity
        self.final_productivity = final_productivity
        self.termination_reason = termination_reason
        if rounds_survived is not None:
            self.rounds_survived = max(self.rounds_survived, rounds_survived)

    def build_summary(self, episode_id: str, **overrides: Any) -> EpisodeMetrics:
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
        }
        values.update(overrides)
        return EpisodeMetrics(**values)
