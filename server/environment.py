import numpy as np
from openenv.env import Env

from core.game import NationGame
from server.models import NationState, NationAction, EventModel


class NationEnvironment(Env):
    """
    OpenEnv wrapper for the Nation Simulator core game engine.
    Translates continuous agent bids (Softmax) into exact treasury percentages.
    """

    def __init__(self, seed: int | None = None):
        super().__init__()
        self.game = NationGame(seed=seed)
        self.sectors = self.game.config.SECTOR_ORDER

    def _get_state(self, game_state: dict) -> NationState:
        """Converts the raw game state dict into the Pydantic model."""
        events = [
            EventModel(
                name=e["name"],
                severity=e["severity"],
                category=e["category"],
                narrative=e["narrative"]
            )
            for e in game_state.get("events", [])
        ]
        return NationState(
            treasury=game_state["treasury"],
            population=game_state["population"],
            productivity=game_state["productivity"],
            active_events=events,
        )

    def reset(self, **kwargs) -> tuple[NationState, dict]:
        """Resets the environment and returns the initial state."""
        game_state = self.game.reset()
        state = self._get_state(game_state)
        return state, {}

    def step(self, action: NationAction) -> tuple[NationState, float, bool, bool, dict]:
        """
        Executes one step in the environment.
        Applies the Softmax Boundary to map continuous bids to allocations.
        """
        # The Softmax Boundary
        raw_bids = np.array(action.bids)
        
        # Subtract max for numerical stability before exp
        raw_bids_stable = raw_bids - np.max(raw_bids)
        exp_bids = np.exp(raw_bids_stable)
        percentages = exp_bids / np.sum(exp_bids)

        # Retrieve the current treasury from the game's internal state
        # Subtract a tiny epsilon to ensure floating point math during sum() doesn't exceed the balance
        treasury = self.game.state["treasury"] - 1e-6

        # Calculate exact dollar allocations, avoiding floating point overflow
        allocations_dict = {}
        allocated = 0.0
        for i, sector in enumerate(self.sectors):
            if i == len(self.sectors) - 1:
                allocations_dict[sector] = float(treasury - allocated)
            else:
                amt = float(percentages[i] * treasury)
                allocations_dict[sector] = amt
                allocated += amt

        # Step the core deterministic engine
        result = self.game.step(allocations_dict)

        # Convert result back to OpenEnv format
        state = self._get_state(result.to_dict())
        reward = result.reward.total
        
        # Gym/OpenEnv standard: (obs, reward, terminated, truncated, info)
        terminated = result.done
        truncated = False
        info = {
            "termination_reason": result.termination_reason,
            "total_revenue": result.total_revenue,
            "allocations_dict": allocations_dict,
            "reward_breakdown": result.reward.to_dict(),
            "year": result.year,
            "quarter": result.quarter,
        }

        return state, float(reward), terminated, truncated, info
