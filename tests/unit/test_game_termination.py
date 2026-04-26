from __future__ import annotations

from core.config import GameConfig
from core.game import NationGame


class NoEventEngine:
    def generate_events(self, sector_names: list[str]) -> list:
        return []

    def apply_events(self, events: list, sectors: dict, treasury) -> bool:
        return False


def test_bankruptcy_reward_does_not_include_zone_penalties() -> None:
    game = NationGame(config=GameConfig.from_json(), seed=0)
    game.reset()
    game._event_engine = NoEventEngine()
    game.treasury.balance = 1.0

    result = game.step(
        {name: 0.0 for name in game.config.SECTOR_BASELINES},
    )

    assert result.done
    assert result.termination_reason == "BANKRUPTCY"
    assert result.reward.over_allocation_penalty == 0.0
    assert result.reward.under_allocation_penalty == 0.0
    assert result.reward.critical_penalty == GameConfig().BANKRUPTCY_PENALTY
