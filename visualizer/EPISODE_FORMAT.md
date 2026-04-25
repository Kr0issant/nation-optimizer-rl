# Visualizer ↔ Game-engine contract

This document describes what the React visualizer in `visualizer/` expects from
the rest of the project. The viewer can render episodes from two sources:

1. **Live streaming** (default): the FastAPI server in
   `server/visualizer_server.py` runs LLM- or rule-based agents through the
   parliamentary loop and streams per-round records over Server-Sent Events.
2. **Static JSON files**: drag-and-drop a `.json` file (or click
   "Load episode JSON") with the shape described below.

The two paths share the same per-round schema, so anything the live runner
produces can be dropped onto disk and replayed later.

---

## 1. The episode JSON contract

Top-level shape:

```jsonc
{
  "episode_id": "string",
  "seed": 42,
  "policy": "string e.g. 'gpt-4o-mini' or 'PPO/checkpoint-12000'",
  "config": {
    "sectors": [
      { "name": "Social", "full_name": "Social/Municipal", "baseline": 60 },
      ...
    ],
    "pop_0": 1000000,
    "initial_treasury": 1000,
    "baseline_tax": 100,
    "productivity_bounds": [0.5, 2.0],
    "max_rounds": 50
  },
  "rounds": [ /* see §1.1 below */ ],
  "summary": {
    "rounds_survived": 50,
    "total_reward": 12345.6,
    "final_treasury": 2200,
    "final_prosperity": 0.0021,
    "final_productivity": 1.42,
    "final_population": 1080000,
    "termination_reason": "MAX_ROUNDS"
  }
}
```

### 1.1 Per-round shape

Each entry in `rounds[]` is one full step (Phases 1–9 of the spec):

```jsonc
{
  "round_num": 1,
  "year": 1,
  "quarter": 1,

  // Phase 1 — events
  "events": [
    {
      "round": 1,
      "id": "war",
      "name": "War",
      "severity": 4,
      "affected_sectors": { "Defense": 2.5, "Agriculture": 1.3 },
      "category": "moderate",
      "narrative": "Enemy forces…",
      "treasury_injection": 0,
      "is_positive": false
    }
  ],
  "crisis_occurred": false,
  "treasury_injection": 0,

  // Phase 2 — debate
  "debate": [
    { "agent_id": "Health", "department": "Health", "message": "…" }
  ],

  // Phases 3–4 — proposals + voting
  "proposal_order": ["Defense", "Health", "Education", "Commerce", "Social", "Agriculture"],
  "proposals": [
    {
      "proposal_id": "r1_Defense",
      "agent_id": "Defense",
      "department": "Defense",
      "amount": 320,
      "justification": "…",
      "status": "approved",
      "rejection_reason": null,
      "votes": { "Health": "YES", "Defense": "ABSTAIN", ... }
    }
  ],
  "votes": [
    {
      "proposal_id": "r1_Defense",
      "agent_id": "Health",
      "department": "Health",
      "vote": "YES"
    }
  ],
  "vote_results": [
    {
      "proposal_id": "r1_Defense",
      "department": "Defense",
      "amount": 320,
      "yes": 4, "no": 1, "abstain": 1,
      "status": "APPROVED"
    }
  ],

  // Phases 5–8 — execution + revenue + surplus
  "allocations":       { "Defense": 320, "Health": 95, ... },
  "consumptions":      { "Defense": 250, "Health": 90, ... },
  "revenues":          { "Defense": 480, "Health": 130, ... },
  "revenue_factors":   { "Defense": 1.50, "Health": 1.36, ... },
  "thresholds": {
    "Defense": { "critical": 100, "demand": 250, "surplus": 375, "wastage": 625 },
    ...
  },
  "event_multipliers": { "Defense": 2.5, "Agriculture": 1.3, ... },

  "treasury_before": 1000.0,
  "treasury_after":  1180.4,
  "total_allocation": 740,
  "total_revenue":    1020.4,
  "surplus_returned":  60.0,
  "population":      1004000,
  "productivity":      1.04,
  "avg_revenue_factor":1.21,
  "prosperity":        0.00102,

  // Phase 9 — reward + termination
  "reward": {
    "base_reward":         0.00102,
    "productivity_bonus":  2.0,
    "survival_bonus":      10.0,
    "over_alloc_penalty":  0,
    "under_alloc_penalty": -10,
    "critical_penalty":    0,
    "total":               2.001
  },
  "cumulative_reward": 2.001,

  "done": false,
  "termination_reason": null,
  "critical_failure_in_budget": false
}
```

### 1.2 Validation rules the loader enforces

`App.jsx::onLoadFile` requires:

- `parsed.rounds` is an array (may be empty for a freshly-started live run).
- `parsed.config.sectors` exists.

Everything else is run through `src/utils/normalizeEpisode.js`, which derives
the optional fields below from the spec formulas in
`specification/04_ECONOMY_MODEL.md`. The engine's lean output is enough.

### 1.3 Required vs derived fields (per round)

| Field | Required | If missing, derived as |
|---|---|---|
| `round_num` | ✓ (or implied by index) | `index + 1` |
| `treasury` *or* `treasury_after` | ✓ | uses whichever is present |
| `treasury_before` | – | previous round's `treasury_after` (`config.initial_treasury` for round 1) |
| `allocations[s]`, `revenues[s]`, `revenue_factors[s]`, `consumptions[s]` | ✓ | – |
| `demands[s]` *or* `thresholds[s]` | ✓ (one of) | thresholds derived as `{0.4, 1.0, 1.5, 2.5} × demand` (spec 04) |
| `event_multipliers[s]` | – | aggregated multiplicatively from `events[].affected_sectors` |
| `total_allocation`, `total_revenue`, `surplus_returned` | – | summed from per-sector dicts |
| `prosperity` | – | `total_revenue / population` (spec 09 base reward) |
| `avg_revenue_factor` | – | mean of `revenue_factors[s]` |
| `cumulative_reward` | – | running sum of `reward.total` |
| `events[].is_positive` | – | true iff `treasury_injection > 0` or `category == "positive"` or every multiplier `< 1` |
| `events[].treasury_injection` | – | `0` |
| `debate`, `proposal_order`, `proposals`, `votes`, `vote_results` | – | empty (panel renders gracefully) |
| `done`, `termination_reason`, `reward.*` | – | falsy / zero |

**Critical-failure semantics** (per `core/game.py::_terminate()` + spec 04):
the engine returns the round with `revenues = 0`, `revenue_factors = 0`,
`consumptions = 0`, `surplus_returned = 0` for every sector and **does not
debit the treasury** (the check fires in Phase 5a, before Phase 5b debit).
The visualizer detects this with `done && termination_reason.startsWith("CRITICAL_FAILURE")`,
flags the offending sector(s) (those with `allocation < critical`), greys out
the rest, and labels the treasury cell as "frozen — failure before debit".

---

## 2. Live streaming

The visualizer talks to `server/visualizer_server.py` over a tiny REST + SSE
surface. The Vite dev server already proxies `/api/*` to
`http://127.0.0.1:8001` (override with `VIZ_BACKEND_URL`).

### 2.1 Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Liveness check. |
| `GET` | `/api/config` | Visualizer-shaped `config` block (sectors, baselines, …). |
| `GET` | `/api/modes` | Available inference modes (`llm` + rule-based baselines). |
| `GET` | `/api/runs` | List recent runs. |
| `POST` | `/api/runs` | Start a new run. Body: `{mode, model_id?, seed, max_rounds, temperature}`. Returns `{run_id, ...}`. |
| `GET` | `/api/runs/{id}/snapshot` | Full episode-so-far in the §1 shape. |
| `GET` | `/api/runs/{id}/stream` | SSE stream — see §2.2. |

### 2.2 SSE event types

Each event arrives as `event: <type>\ndata: <json>\n\n`. The browser client in
`src/utils/api.js` dispatches them into typed callbacks.

| `event` | Payload | Notes |
|---|---|---|
| `start` | `{run_id, policy, mode, seed, config, max_rounds}` | Sent once on connection. |
| `round` | A single per-round record (§1.1). | One per completed round. |
| `summary` | The §1 `summary` block. | Sent once when the episode finishes. |
| `error` | `{message: string}` | Adapter or engine failure. |
| `done`  | `{reason: "complete" \| "error" \| "already_closed"}` | Always the last event. |

Late subscribers receive the full event history first (so refreshing the page
mid-run replays from the beginning), then live updates.

### 2.3 Inference modes

Modes returned from `/api/modes`:

- `llm` — drives every minister with a Hugging Face Inference API model.
  Requires `HF_TOKEN` in the server `.env`; reads `HF_MODEL_ID` as the default
  model id (the form lets you override it per-run).
- `equal_split`, `optimal_zone`, `conservative`, `greedy` — rule-based
  baselines from `agents/rule_based/`. Useful for offline demos.

### 2.4 Running locally

Two terminals:

```bash
# Terminal 1 — backend (FastAPI + SSE on :8001)
python -m scripts.run_visualizer_server

# Terminal 2 — frontend (Vite dev server on :5173)
cd visualizer
npm install     # one time
npm run dev
```

Open <http://localhost:5173>, pick a policy in the **Live inference** card, and
press **Start run**. Rounds will stream into the dashboard as they're produced.

---

## 3. Static JSON files

The static loader is unchanged. To export a recorded run, hit
`GET /api/runs/{id}/snapshot` and save the response — the file matches the
shape in §1 and can be dragged back into the visualizer at any time.

---

## 4. Development notes

- `vite.config.js` has `server.watch.usePolling: true` because the project
  lives on a WSL-mounted Windows drive where `fs.watch()` throws `EISDIR`.
  Remove it on a normal filesystem to lower idle CPU.
- For the very first run on Windows + WSL, install dependencies *inside* WSL
  (`wsl npm install`) to avoid `EPERM`/`EISDIR` cleanup errors, then run the
  build/dev server from either side.
- The proxy block in `vite.config.js` strips response buffering for the
  `/stream` endpoint so SSE chunks arrive immediately even through the dev
  proxy.
