"""FastAPI app that streams live LLM episodes to the React visualizer.

This is intentionally a *separate* FastAPI app from
:mod:`server.app` (which mounts the OpenEnv environment for RL training and
remote rollout clients). It exposes a small, browser-friendly REST + SSE
surface so the React dashboard at ``visualizer/`` can:

  - List the rule-based and LLM-backed inference modes.
  - Start a new live run with a chosen seed and policy.
  - Stream per-round JSON records over Server-Sent Events while the run is
    still in progress.
  - Re-fetch the full episode-so-far when the page is refreshed mid-run.

Run it locally with::

    uvicorn server.visualizer_server:app --host 0.0.0.0 --port 8001

Or via the convenience wrapper::

    python -m scripts.run_visualizer_server
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from server.live_runner import (
    LiveRun,
    LiveRunManager,
    build_config_dict,
)

load_dotenv()

LOG = logging.getLogger(__name__)


# ── Mode metadata exposed to the UI ─────────────────────────────────────────


_RULE_BASED_MODES = (
    {
        "id": "equal_split",
        "label": "Equal split",
        "description": "Each minister proposes treasury / 6 every round.",
        "requires_credentials": False,
    },
    {
        "id": "optimal_zone",
        "label": "Optimal zone (1.3× baseline)",
        "description": "Targets the profit zone above demand without entering wastage.",
        "requires_credentials": False,
    },
    {
        "id": "conservative",
        "label": "Conservative (baseline)",
        "description": "Each minister proposes its own department baseline.",
        "requires_credentials": False,
    },
    {
        "id": "greedy",
        "label": "Greedy",
        "description": "Greedy proposer baseline; useful for adversarial demos.",
        "requires_credentials": False,
    },
)


def _llm_mode_entry() -> dict[str, Any]:
    return {
        "id": "llm",
        "label": "LLM (Hugging Face)",
        "description": "Drives every minister with the configured HF model.",
        "requires_credentials": True,
        "default_model_id": os.environ.get("HF_MODEL_ID"),
        "credentials_present": bool(os.environ.get("HF_TOKEN"))
        and bool(os.environ.get("HF_MODEL_ID")),
    }


# ── Request/response models ─────────────────────────────────────────────────


class StartRunBody(BaseModel):
    mode: str = Field(
        description="One of the ids returned by GET /api/modes."
    )
    model_id: Optional[str] = Field(default=None, description="HF model id (LLM mode).")
    seed: int = Field(default=42, ge=0)
    max_rounds: int = Field(default=20, ge=1, le=50)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)


class StartRunResponse(BaseModel):
    run_id: str
    mode: str
    policy: str
    seed: int
    max_rounds: int
    config: dict[str, Any]


# ── App + manager ───────────────────────────────────────────────────────────


app = FastAPI(
    title="Nation Optimizer · Visualizer",
    description="Streams live LLM-driven parliamentary episodes to the React dashboard.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = LiveRunManager()


# ── Routes ──────────────────────────────────────────────────────────────────


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "ts": time.time()}


@app.get("/api/config")
def config() -> dict[str, Any]:
    """Static game config (sectors, baselines, etc.) for the empty-state UI."""
    return build_config_dict()


@app.get("/api/modes")
def modes() -> dict[str, Any]:
    return {
        "modes": [_llm_mode_entry(), *_RULE_BASED_MODES],
    }


@app.get("/api/runs")
def list_runs() -> dict[str, Any]:
    return {"runs": manager.list_runs()}


@app.post("/api/runs", response_model=StartRunResponse)
def start_run(body: StartRunBody) -> StartRunResponse:
    if body.mode == "llm":
        token = os.environ.get("HF_TOKEN")
        if not token:
            raise HTTPException(
                status_code=400,
                detail=(
                    "LLM mode requires HF_TOKEN in the server environment. "
                    "Either set it in .env or pick a rule-based mode."
                ),
            )
        model_id = body.model_id or os.environ.get("HF_MODEL_ID")
        if not model_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "LLM mode requires model_id (or HF_MODEL_ID env var)."
                ),
            )
    else:
        token = None
        model_id = body.model_id

    try:
        run = manager.create(
            mode=body.mode,
            model_id=model_id,
            seed=body.seed,
            max_rounds=body.max_rounds,
            temperature=body.temperature,
            token=token,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return StartRunResponse(
        run_id=run.run_id,
        mode=run.mode,
        policy=run.policy,
        seed=run.seed,
        max_rounds=run.max_rounds,
        config=run.config,
    )


@app.get("/api/runs/{run_id}/snapshot")
def snapshot(run_id: str) -> dict[str, Any]:
    run = manager.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Unknown run_id {run_id!r}.")
    return run.snapshot()


@app.get("/api/runs/{run_id}/stream")
async def stream(run_id: str, request: Request) -> StreamingResponse:
    """SSE stream of ``start | round | summary | error | done`` events."""
    run = manager.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Unknown run_id {run_id!r}.")

    return StreamingResponse(
        _sse_iterator(run, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ── SSE plumbing ────────────────────────────────────────────────────────────


async def _sse_iterator(run: LiveRun, request: Request):
    """Yield Server-Sent Events for one client subscriber.

    A heartbeat comment (``:keep-alive``) is sent every ~15s so proxies don't
    cut the connection during long LLM generations.
    """
    import asyncio

    queue = run.subscribe()
    try:
        last_heartbeat = time.time()
        while True:
            if await request.is_disconnected():
                break

            event = await asyncio.get_event_loop().run_in_executor(
                None, _drain, queue, 1.0
            )

            if event is not None:
                yield _format_sse(event)
                if event.get("type") == "done":
                    break
                continue

            now = time.time()
            if now - last_heartbeat > 15:
                yield ": keep-alive\n\n"
                last_heartbeat = now
    finally:
        run.unsubscribe(queue)


def _drain(queue: Any, timeout: float) -> Optional[dict[str, Any]]:
    from queue import Empty

    try:
        return queue.get(timeout=timeout)
    except Empty:
        return None


def _format_sse(event: dict[str, Any]) -> str:
    """Format a dict as a Server-Sent Event with an explicit ``event:`` name."""
    event_type = event.get("type", "message")
    payload = event.get("data", {})
    body = json.dumps(payload, default=_json_default)
    return f"event: {event_type}\ndata: {body}\n\n"


def _json_default(value: Any) -> Any:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return value.to_dict()
    if hasattr(value, "value"):
        return value.value
    return str(value)


__all__ = ["app", "manager"]
