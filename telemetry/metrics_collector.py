"""Small metric accumulator for seeded evaluation runs."""

from dataclasses import dataclass


@dataclass(slots=True)
class MetricsCollector:
    total_reward: float = 0.0
    rounds_survived: int = 0

    def record_step(self, reward: float, round_number: int) -> None:
        self.total_reward += reward
        self.rounds_survived = max(self.rounds_survived, round_number)
