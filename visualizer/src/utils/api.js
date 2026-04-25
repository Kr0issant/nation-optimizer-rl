// api.js
// ----------------------------------------------------------------------------
// Thin browser client for the FastAPI server in `server/visualizer_server.py`.
//
//   - `getModes()`           — list available inference modes (LLM + baselines).
//   - `getConfig()`          — sectors/baselines/etc. for the empty-state shell.
//   - `startRun(opts)`       — POST /api/runs and return the new {run_id, ...}.
//   - `streamRun(runId, on)` — open an EventSource and dispatch typed events.
//   - `getSnapshot(runId)`   — fetch the full episode-so-far (used on reload).
//
// The visualizer assumes Vite's dev proxy maps /api/* to the backend (see
// `vite.config.js`). In production builds the same path works as long as the
// FastAPI server is reverse-proxied under the same origin as the static UI.
// ----------------------------------------------------------------------------

const BASE = '/api';

async function jsonOrThrow(res) {
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.detail) message = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* empty body — fall back to status */
    }
    throw new Error(message);
  }
  return res.json();
}

export async function getHealth() {
  return jsonOrThrow(await fetch(`${BASE}/health`));
}

export async function getConfig() {
  return jsonOrThrow(await fetch(`${BASE}/config`));
}

export async function getModes() {
  return jsonOrThrow(await fetch(`${BASE}/modes`));
}

export async function listRuns() {
  return jsonOrThrow(await fetch(`${BASE}/runs`));
}

export async function startRun({
  mode,
  modelId = null,
  seed = 42,
  maxRounds = 20,
  temperature = 0.2,
}) {
  const res = await fetch(`${BASE}/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      mode,
      model_id: modelId,
      seed,
      max_rounds: maxRounds,
      temperature,
    }),
  });
  return jsonOrThrow(res);
}

export async function getSnapshot(runId) {
  return jsonOrThrow(await fetch(`${BASE}/runs/${runId}/snapshot`));
}

/**
 * Open an SSE connection to a live run.
 *
 * `handlers` may contain any subset of:
 *   { onStart, onRound, onActivity, onSummary, onError, onDone, onConnectionError }
 *
 * `onActivity(data)` fires for each within-round action:
 *   data.kind = 'round_start' | 'debate' | 'proposal' | 'vote'
 *
 * Returns an object with a `close()` method to tear the connection down.
 */
export function streamRun(runId, handlers = {}) {
  const url = `${BASE}/runs/${runId}/stream`;
  const source = new EventSource(url);

  const route = (type, ev) => {
    let data = {};
    try {
      data = ev.data ? JSON.parse(ev.data) : {};
    } catch (err) {
      handlers.onConnectionError?.(err);
      return;
    }
    switch (type) {
      case 'start':
        handlers.onStart?.(data);
        break;
      case 'activity':
        handlers.onActivity?.(data);
        break;
      case 'round':
        handlers.onRound?.(data);
        break;
      case 'summary':
        handlers.onSummary?.(data);
        break;
      case 'error':
        handlers.onError?.(data);
        break;
      case 'done':
        handlers.onDone?.(data);
        source.close();
        break;
      default:
        break;
    }
  };

  ['start', 'activity', 'round', 'summary', 'error', 'done'].forEach(type => {
    source.addEventListener(type, e => route(type, e));
  });

  source.onerror = err => {
    handlers.onConnectionError?.(err);
  };

  return {
    close: () => source.close(),
    raw: source,
  };
}
