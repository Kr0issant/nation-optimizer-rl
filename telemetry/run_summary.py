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
