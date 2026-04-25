"""FastAPI entrypoint for serving the Nation Optimizer OpenEnv environment."""

from __future__ import annotations

import os

try:
    from openenv.core.env_server import create_app
except ImportError:  # pragma: no cover - exercised only before dependencies are installed
    from openenv.core.env_server.http_server import create_app

try:
    from .environment import DEFAULT_ENV_NAME, NationOpenEnv
    from .models import NationAction, NationObservation
except ImportError:  # pragma: no cover - supports Docker PYTHONPATH=/app
    from server.environment import DEFAULT_ENV_NAME, NationOpenEnv
    from server.models import NationAction, NationObservation


MAX_CONCURRENT_ENVS = int(os.getenv("MAX_CONCURRENT_ENVS", "4"))

app = create_app(
    NationOpenEnv,
    NationAction,
    NationObservation,
    env_name=DEFAULT_ENV_NAME,
    max_concurrent_envs=MAX_CONCURRENT_ENVS,
)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))


if __name__ == "__main__":
    main()
