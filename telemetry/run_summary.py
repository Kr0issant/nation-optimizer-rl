"""Helpers for serializing completed rollout summaries."""

from __future__ import annotations

from dataclasses import dataclass, field

from schemas.metrics import EpisodeMetrics


@dataclass(frozen=True, slots=True)
class RunSummary:
    run_id: str
    episodes: tuple[EpisodeMetrics, ...] = field(default_factory=tuple)

    @property
    def episode_count(self) -> int:
        return len(self.episodes)

    @property
    def mean_total_reward(self) -> float:
        if not self.episodes:
            return 0.0
        return sum(episode.total_reward for episode in self.episodes) / self.episode_count

    @property
    def mean_rounds_survived(self) -> float:
        if not self.episodes:
            return 0.0
        return (
            sum(episode.rounds_survived for episode in self.episodes)
            / self.episode_count
        )

    @property
    def critical_failure_rate(self) -> float:
        return self._rate("critical_failure_count")

    @property
    def bankruptcy_rate(self) -> float:
        return self._rate("bankruptcy_count")

    @property
    def shutdown_rate(self) -> float:
        return self._rate("shutdown_count")

    @property
    def mean_final_prosperity(self) -> float | None:
        return self._mean_optional("final_prosperity")

    @property
    def mean_average_revenue_factor(self) -> float | None:
        return self._mean_optional("average_revenue_factor")

    @property
    def mean_treasury_stability(self) -> float | None:
        return self._mean_optional("treasury_stability")

    @property
    def mean_productivity_growth(self) -> float | None:
        return self._mean_optional("productivity_growth")

    @property
    def invalid_action_count(self) -> int:
        return self._sum("invalid_action_count")

    @property
    def parse_error_count(self) -> int:
        return self._sum("parse_error_count")

    @property
    def prompt_tokens(self) -> int:
        return self._sum("prompt_tokens")

    @property
    def completion_tokens(self) -> int:
        return self._sum("completion_tokens")

    @property
    def total_tokens(self) -> int:
        return self._sum("total_tokens")

    @property
    def debate_message_count(self) -> int:
        return self._sum("debate_message_count")

    @property
    def proposals_passed_count(self) -> int:
        return self._sum("proposals_passed_count")

    def _rate(self, field_name: str) -> float:
        if not self.episodes:
            return 0.0
        return self._sum(field_name) / self.episode_count

    def _sum(self, field_name: str) -> int:
        return sum(getattr(episode, field_name) for episode in self.episodes)

    def _mean_optional(self, field_name: str) -> float | None:
        values = [
            value
            for episode in self.episodes
            if (value := getattr(episode, field_name)) is not None
        ]
        if not values:
            return None
        return sum(values) / len(values)
