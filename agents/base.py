"""Common adapter interface for all policy implementations."""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from schemas.actions import Action
from schemas.observations import Observation


class PolicyAdapter(ABC):
    """Consumes an observation and emits one structured environment action."""

    @abstractmethod
    def act(
        self,
        observation: Observation,
        valid_actions: Iterable[str],
        agent_id: str,
    ) -> Action:
        raise NotImplementedError

    def reset(self) -> None:
        """Reset any per-episode adapter state."""
