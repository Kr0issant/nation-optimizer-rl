"""Final Unified Server: OpenEnv API + React Visualizer + Live Streaming."""

import os
import json
import time
import logging
import asyncio
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openenv.core.env_server import create_app

# Import core environment and visualizer logic
from server.environment import DEFAULT_ENV_NAME, NationOpenEnv
from server.models import NationAction, NationObservation
from server.live_runner import LiveRun, LiveRunManager, build_config_dict
from server.visualizer_server import StartRunBody, StartRunResponse, _RULE_BASED_MODES, _llm_mode_entry, _json_default

load_dotenv()
LOG = logging.getLogger(__name__)

# --- 1. INITIALIZE OPENENV CORE ---
app = create_app(
    NationOpenEnv,
    NationAction,
    NationObservation,
    env_name=DEFAULT_ENV_NAME,
    max_concurrent_envs=int(os.getenv("MAX_CONCURRENT_ENVS", "4")),
)

# Add CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. INITIALIZE VISUALIZER MANAGER ---
manager = LiveRunManager()

# --- 3. VISUALIZER API ROUTES (/api/*) ---

@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "ts": time.time()}

@app.get("/api/config")
def config() -> dict[str, Any]:
    return build_config_dict()

@app.get("/api/modes")
def modes() -> dict[str, Any]:
    return {"modes": [_llm_mode_entry(), *_RULE_BASED_MODES]}

@app.get("/api/runs")
def list_runs() -> dict[str, Any]:
    return {"runs": manager.list_runs()}

@app.post("/api/runs", response_model=StartRunResponse)
def start_run(body: StartRunBody) -> StartRunResponse:
    if body.mode == "llm":
        token = os.environ.get("HF_TOKEN")
        if not token:
            raise HTTPException(status_code=400, detail="LLM mode requires HF_TOKEN.")
        model_id = body.model_id or os.environ.get("HF_MODEL_ID")
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
        return StartRunResponse(
            run_id=run.run_id,
            mode=run.mode,
            policy=run.policy,
            seed=run.seed,
            max_rounds=run.max_rounds,
            config=run.config,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.get("/api/runs/{run_id}/snapshot")
def snapshot(run_id: str) -> dict[str, Any]:
    run = manager.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Unknown run {run_id}")
    return run.snapshot()

@app.get("/api/runs/{run_id}/stream")
async def stream(run_id: str, request: Request) -> StreamingResponse:
    run = manager.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Unknown run {run_id}")

    async def _sse_iterator():
        queue = run.subscribe()
        try:
            last_heartbeat = time.time()
            while True:
                if await request.is_disconnected():
                    break
                
                # Drain queue (non-blocking in executor)
                event = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: (None if queue.empty() else queue.get())
                )

                if event is not None:
                    event_type = event.get("type", "message")
                    payload = event.get("data", {})
                    body = json.dumps(payload, default=_json_default)
                    yield f"event: {event_type}\ndata: {body}\n\n"
                    if event_type == "done":
                        break
                    continue

                if time.time() - last_heartbeat > 15:
                    yield ": keep-alive\n\n"
                    last_heartbeat = time.time()
                await asyncio.sleep(0.1)
        finally:
            run.unsubscribe(queue)

    return StreamingResponse(
        _sse_iterator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )

# --- 4. STATIC FRONTEND MOUNTING ---
dist_path = Path(__file__).parent.parent / "visualizer" / "dist"
if dist_path.exists():
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="visualizer")
    LOG.info(f"⚛️  React Visualizer mounted from {dist_path}")
else:
    LOG.warning(f"⚠️  Visualizer build not found at {dist_path}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
