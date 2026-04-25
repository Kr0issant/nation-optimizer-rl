"""FastAPI entrypoint for the Nation Optimizer OpenEnv server."""

from __future__ import annotations

import os
from typing import Any

from server.environment import NationEnvironment
from server.models import ParliamentaryAction, ParliamentaryObservation

try:
    from openenv.core.env_server import create_app
except ImportError:  # pragma: no cover - compatibility fallback
    try:
        from openenv_core import create_app
    except ImportError:  # pragma: no cover
        create_app = None


ENV_NAME = "nation_optimizer_rl"
MAX_CONCURRENT_ENVS = int(os.getenv("MAX_CONCURRENT_ENVS", "4"))


class OpenEnvNationEnvironment(NationEnvironment):
    """OpenEnv HTTP adapter over the Gymnasium-style NationEnvironment."""

    def reset(
        self,
        seed: int | None = None,
        episode_id: str | None = None,
        **kwargs: Any,
    ) -> ParliamentaryObservation:
        del episode_id
        observation, info = super().reset(seed=seed, **kwargs)
        observation.metadata["info"] = info
        return observation

    def step(
        self,
        action: ParliamentaryAction,
        timeout_s: float | None = None,
        **kwargs: Any,
    ) -> ParliamentaryObservation:
        del timeout_s, kwargs
        observation, reward, terminated, truncated, info = super().step(action)
        observation.reward = reward
        observation.done = terminated or truncated
        observation.metadata["terminated"] = terminated
        observation.metadata["truncated"] = truncated
        observation.metadata["info"] = info
        return observation


def _manual_app() -> Any:
    """Small HTTP fallback for local smoke when OpenEnv is unavailable."""
    from fastapi import FastAPI

    app = FastAPI(title=ENV_NAME)
    env = NationEnvironment()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "healthy"}

    @app.post("/reset")
    def reset(payload: dict[str, Any] | None = None) -> dict[str, Any]:
        observation, info = env.reset(**(payload or {}))
        return {
            "observation": observation.model_dump(mode="json"),
            "reward": observation.reward,
            "done": observation.done,
            "info": info,
        }

    @app.post("/step")
    def step(payload: dict[str, Any]) -> dict[str, Any]:
        action_data = payload.get("action", payload)
        observation, reward, terminated, truncated, info = env.step(
            ParliamentaryAction(**action_data)
        )
        return {
            "observation": observation.model_dump(mode="json"),
            "reward": reward,
            "done": terminated or truncated,
            "terminated": terminated,
            "truncated": truncated,
            "info": info,
        }

    @app.get("/state")
    def state() -> dict[str, Any]:
        return env.state.model_dump(mode="json")

    return app


if create_app is None:
    app = _manual_app()
else:
    app = create_app(
        OpenEnvNationEnvironment,
        ParliamentaryAction,
        ParliamentaryObservation,
        env_name=ENV_NAME,
        max_concurrent_envs=MAX_CONCURRENT_ENVS,
    )


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))


if __name__ == "__main__":
    main()
