"""Typed OpenEnv client for Nation Optimizer RL."""

from __future__ import annotations

from typing import Any

from openenv.core import EnvClient, StepResult

from server.models import NationState, ParliamentaryAction, ParliamentaryObservation


class NationOptimizerEnv(
    EnvClient[ParliamentaryAction, ParliamentaryObservation, NationState]
):
    """Client for local servers, Docker containers, and Hugging Face Spaces."""

    def _step_payload(self, action: ParliamentaryAction) -> dict[str, Any]:
        return action.model_dump(mode="json", exclude_none=True)

    def _parse_result(
        self,
        payload: dict[str, Any],
    ) -> StepResult[ParliamentaryObservation]:
        observation = ParliamentaryObservation(**payload["observation"])
        return StepResult(
            observation=observation,
            reward=payload.get("reward", observation.reward),
            done=payload.get("done", observation.done),
        )

    def _parse_state(self, payload: dict[str, Any]) -> NationState:
        return NationState(**payload)
