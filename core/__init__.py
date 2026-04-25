"""
core — Pure game engine for the Nation Simulator.

No framework dependencies.  The entire game can be run with::

    from core import NationGame

    game = NationGame(seed=42)
    obs = game.reset()

    allocations = {name: baseline * 1.3 for name, baseline in game.config.SECTOR_BASELINES.items()}
    result = game.step(allocations)
    print(result.reward.total, result.done)
"""

from .config import DEFAULT_CONFIG, GameConfig
from .events import Event, EventEngine
from .game import NationGame, StepResult
from .population import PopulationTracker
from .productivity import ProductivityTracker
from .revenue import calculate_revenue, compute_thresholds, revenue_factor
from .reward import RewardBreakdown, RewardResult, compute_reward
from .sector import Sector
from .treasury import Treasury

__all__ = [
    "NationGame",
    "StepResult",
    "GameConfig",
    "DEFAULT_CONFIG",
    "Sector",
    "Treasury",
    "EventEngine",
    "Event",
    "ProductivityTracker",
    "PopulationTracker",
    "revenue_factor",
    "calculate_revenue",
    "compute_thresholds",
    "compute_reward",
    "RewardBreakdown",
    "RewardResult",
]
