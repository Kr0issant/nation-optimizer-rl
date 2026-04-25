"""OpenEnv client for the Nation Optimizer environment."""

from __future__ import annotations

from typing import Any

from openenv.core.client_types import StepResult
from openenv.core.env_client import EnvClient

from server.models import NationAction, NationObservation, NationState


class NationOptimizerEnv(EnvClient[NationAction, NationObservation, NationState]):
    """Typed OpenEnv client for local servers and Hugging Face Spaces."""

    def _step_payload(self, action: NationAction) -> dict[str, Any]:
        return action.model_dump(mode="json", exclude_none=True)

    def _parse_result(self, payload: dict[str, Any]) -> StepResult[NationObservation]:
        observation = NationObservation(**payload["observation"])
        return StepResult(
            observation=observation,
            reward=payload.get("reward", observation.reward),
            done=payload.get("done", observation.done),
        )

    def _parse_state(self, payload: dict[str, Any]) -> NationState:
        return NationState(**payload)
