import random
from server.models import NationAction, NationState

class RandomAgent:
    """A baseline agent that outputs random continuous bids for the 6 sectors."""
    
    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)
        
    def act(self, state: NationState) -> NationAction:
        """Returns 6 random floats between -1.0 and 1.0."""
        bids = [self.rng.uniform(-1.0, 1.0) for _ in range(6)]
        return NationAction(bids=bids)
