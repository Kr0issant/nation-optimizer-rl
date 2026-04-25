"""Episode and benchmark metric schemas."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EpisodeMetrics:
    episode_id: str
    rounds_survived: int
    total_reward: float
    final_prosperity: float | None = None
    final_treasury: float | None = None
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
    average_revenue_factor: float | None = None
    treasury_stability: float | None = None
    productivity_growth: float | None = None
    debate_message_count: int = 0
    proposals_passed_count: int = 0
