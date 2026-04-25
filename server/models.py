from pydantic import BaseModel, Field


class EventModel(BaseModel):
    """Pydantic representation of an active game event."""
    name: str
    severity: int
    category: str
    narrative: str


class NationState(BaseModel):
    """The observation state returned to the RL agent."""
    treasury: float
    population: int
    productivity: float
    active_events: list[EventModel] = Field(default_factory=list)


class NationAction(BaseModel):
    """The continuous action space for the 6 sectors."""
    bids: list[float] = Field(
        ...,
        min_length=6,
        max_length=6,
        description="Continuous bids from each of the 6 sectors."
    )
