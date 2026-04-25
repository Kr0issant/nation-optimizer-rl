from __future__ import annotations

from core.config import GameConfig
from core.game import NationGame


class NoEventEngine:
    def generate_events(self, sector_names: list[str]) -> list:
        return []

    def apply_events(self, events: list, sectors: dict, treasury) -> bool:
        return False


def test_critical_failure_reward_does_not_include_zone_penalties() -> None:
    game = NationGame(config=GameConfig.from_json(), seed=0)
    game.reset()
    game._event_engine = NoEventEngine()

    result = game.step(
        {
            "Social": 300.0,
            "Agriculture": 70.0,
            "Health": 90.0,
            "Education": 80.0,
            "Defense": 30.0,
            "Commerce": 75.0,
        },
    )

    assert result.done
    assert result.termination_reason == "CRITICAL_FAILURE"
    assert result.reward.over_allocation_penalty == 0.0
    assert result.reward.under_allocation_penalty == 0.0
    assert result.reward.critical_penalty == -1000.0
