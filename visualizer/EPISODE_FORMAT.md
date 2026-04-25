# Visualizer ↔ Game-engine contract

This document describes what the React visualizer in `visualizer/` expects from
the rest of the project, and lists the **backend pieces that still need to be
built** so the viewer can load *real* training rollouts instead of the
synthetic episode in `src/sampleRun.js`.

The synthetic sample is intentionally shaped 1:1 like the eventual exporter
output, so once the pieces below are in place the visualizer needs **zero
changes** — drag-and-drop a `.json` file (or click "Load episode JSON") and the
dashboard will render it.

---

## 1. The episode JSON contract

The visualizer reads a single JSON object per episode. Top-level shape:

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

Each entry in `rounds[]` is one full step (Phases 1–6 of the spec):

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
      "category": "moderate",     // minor | moderate | critical | compound
      "narrative": "Enemy forces…",
      "treasury_injection": 0,    // > 0 only for positive events
      "is_positive": false
    }
  ],
  "crisis_occurred": false,
  "treasury_injection": 0,        // sum of positive-event injections

  // Phase 2 — debate
  "debate": [
    { "agent_id": "minister_health", "department": "Health", "message": "…" }
  ],

  // Phases 3–4 — proposals + voting
  "proposal_order": ["Defense", "Health", "Education", "Commerce", "Social", "Agriculture"],
  "proposals": [
    {
      "proposal_id": "r1_Defense",
      "agent_id": "minister_defense",
      "department": "Defense",
      "amount": 320,
      "justification": "…",
      "timestamp_phase": 3
    }
  ],
  "votes": [
    {
      "proposal_id": "r1_Defense",
      "agent_id": "minister_health",
      "department": "Health",
      "vote": "YES"               // YES | NO | ABSTAIN
    }
  ],
  "vote_results": [
    {
      "proposal_id": "r1_Defense",
      "department": "Defense",
      "amount": 320,
      "yes": 4, "no": 1, "abstain": 1,
      "status": "APPROVED"        // APPROVED | REJECTED | AUTO_REJECTED_INSUFFICIENT_TREASURY
    }
  ],

  // Phase 5 — execution
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

  // Phase 6 — reward
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
  "termination_reason": null    // string when done=true, e.g. "BANKRUPTCY"
}
```

### 1.2 Validation rules the loader enforces

`App.jsx::onLoadFile` requires:

- `parsed.rounds` is a non-empty array.
- `parsed.config.sectors` exists.

Everything else is run through `src/utils/normalizeEpisode.js`, which derives
the optional fields below from the spec formulas in
`specification/04_ECONOMY_MODEL.md`. So the **engine's lean output** is enough.

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

## 2. Game-engine pieces still missing

The current backend only has `core/__init__.py`, `core/game.py`, and the two
JSON catalogs. To produce the JSON above we still need the following modules.
Suggested layout (mirrors `FILE_STRUCTURE.md`):

### 2.1 `core/` — game internals

| File | Purpose | Status |
|---|---|---|
| `core/game.py` | `NationGame` + `StepResult` (treasury, allocations, revenues, …) | **exists** |
| `core/config.py` | `GameConfig` (constants, ratios, JSON loader) | **exists** |
| `core/sectors.json` / `core/events.json` | Catalog data | **exists** |
| `core/sector.py` | `Sector` dataclass + threshold accessors + `compute_revenue` | **exists** |
| `core/treasury.py` | Treasury debit/credit ledger | **exists** |
| `core/events.py` | Event roller (weighted tiers, severity sampling, treasury injection, demand multipliers) | **exists** |
| `core/reward.py` | Per-step reward decomposition with the keys §1.1 expects (`base_reward`, `productivity_bonus`, `survival_bonus`, `over_alloc_penalty`, `under_alloc_penalty`, `critical_penalty`, `total`) | **exists** |
| `core/population.py` | Productivity update, birth/death model | **exists** (referenced in `game.py`) |
| `core/revenue.py` | `revenue_factor()` and `compute_thresholds()` helpers | **exists** (imported by `sector.py`) |
| `core/voting.py` | Plurality with abstentions, self-abstention rule, `AUTO_REJECTED_INSUFFICIENT_TREASURY` | **missing** — orchestrator-level; not used by `game.py` yet |

The engine's `StepResult.to_dict()` already emits the right reward shape. What
it does **not** emit (and what the visualizer derives or tolerates as missing):

- `treasury_before` (single `treasury` is given — the post-state)
- `thresholds[s]` (`demands[s]` only — the rest are derived from spec 04 ratios)
- `event_multipliers[s]` (aggregated from `events[].affected_sectors`)
- `prosperity`, `avg_revenue_factor`, `cumulative_reward` (derived)
- `events[].is_positive` and `events[].treasury_injection` (the engine's
  `_treasury_injection` field is private — `Event.to_dict()` should expose it
  publicly when the recorder is built, otherwise the visualizer falls back to
  category/multiplier heuristics)
- The orchestrator-level fields (`debate`, `proposals`, `votes`,
  `vote_results`, `proposal_order`) — the engine doesn't run a parliament,
  the orchestrator will.

### 2.2 `schemas/` — wire formats

These dataclasses define what the orchestrator records each round:

- `schemas/action.py` — `ProposalAction { department, amount, justification }`,
  `VoteAction { proposal_id, vote, reasoning? }`, `DebateMessage { department, message }`.
- `schemas/observation.py` — what each agent sees in Phase 0
  (treasury, sector states, last round summary, recent events).
- `schemas/reward.py` — the `RewardBreakdown` shape above.
- `schemas/episode.py` — Pydantic / dataclass mirror of §1.1, used as the
  serialisation target for `evaluation/export_episode.py`.

### 2.3 `agents/` — decision-makers

Each minister needs an interface the orchestrator can call:

```python
class MinisterAgent:
    department: str
    def speak(self, obs) -> Optional[DebateMessage]: ...
    def propose(self, obs) -> ProposalAction: ...
    def vote(self, obs, proposal) -> VoteAction: ...
```

Concrete implementations:
- `agents/llm_agent.py` (LLM-backed, used during data collection / play)
- `agents/scripted_agent.py` (heuristic baseline — useful for visualizer demos)
- `agents/policy_agent.py` (loads a trained RL policy)

### 2.4 `core/orchestrator.py` — runs an episode

This is the single biggest missing piece. It owns the per-round loop:

```python
def run_episode(game, agents, *, recorder) -> EpisodeRecord:
    while not game.done:
        events = game.roll_events()
        recorder.events(events)

        for a in agents.shuffled():
            msg = a.speak(game.observation_for(a))
            if msg: recorder.debate(msg)

        order = game.proposal_order()
        proposals = [agents[d].propose(game.observation_for(agents[d])) for d in order]
        recorder.proposals(proposals)

        votes, results = game.run_voting(proposals, agents)
        recorder.votes(votes, results)

        step = game.execute(results)            # returns StepResult
        recorder.step(step)                      # treasury, revenues, reward, …
    return recorder.finalize()
```

The orchestrator is also the natural home for the rotating proposal order,
sequential treasury depletion checks, and `AUTO_REJECTED_INSUFFICIENT_TREASURY`
bookkeeping — all of which the visualizer expects to see in `vote_results[]`.

### 2.5 `telemetry/recorder.py` — capture buffer

A small in-memory buffer that the orchestrator writes to during a run and that
serialises out at the end. Two outputs:

1. `telemetry/runs/<run_id>/episode_<n>.json` — the visualizer-ready file.
2. `telemetry/runs/<run_id>/trajectory_<n>.jsonl` — one line per agent
   action/observation/reward, used by RL training.

The episode JSON is just `EpisodeRecord.model_dump_json(indent=2)`.

### 2.6 `evaluation/export_episode.py` — CLI exporter

A thin entry point so users can produce a viewer-ready file from any episode:

```bash
python -m evaluation.export_episode \
    --policy gpt-4o-mini \
    --seed 42 \
    --max-rounds 50 \
    --out telemetry/runs/demo/episode_001.json
```

It should:

1. Build a `NationGame` from `core/sectors.json` + `core/events.json`.
2. Instantiate the chosen agents.
3. Call `run_episode(...)` with a fresh `Recorder`.
4. Write the JSON to `--out`.

That file can then be dragged into the visualizer.

### 2.7 (Optional) `server/replay_server.py` — live streaming

If we want to watch training rollouts live (rather than after the fact), a
tiny FastAPI/uvicorn server that exposes:

- `GET /episodes` → list of available `episode_*.json`
- `GET /episodes/{id}` → the full JSON
- `GET /stream/{run_id}` → SSE/WebSocket pushing newly recorded rounds

The viewer would only need a "Connect to live run" button; the rest of the UI
stays identical because the per-round shape is unchanged.

---

## 3. End-to-end checklist

To get from "today" to "visualizer shows real episodes":

1. Extract `Sector`, `revenue_factor`, and reward math out of `core/game.py`
   into `core/sector.py` and `core/reward.py` (so the reward keys in §1.1 are
   guaranteed to exist).
2. Add `core/events.py`, `core/voting.py`, `core/population.py`.
3. Define `schemas/{action,observation,reward,episode}.py`.
4. Implement `agents/scripted_agent.py` for the first end-to-end smoke test.
5. Implement `core/orchestrator.py` + `telemetry/recorder.py`.
6. Wire `evaluation/export_episode.py` and run it once with the scripted
   agent.
7. Drag the resulting `episode_001.json` into the visualizer — the existing
   sample data falls away and the dashboard renders the real run.

Until step 7 is reachable, the viewer keeps using `src/sampleRun.js` as a
realistic stand-in. That sample file is the canonical reference for the
expected shape — when in doubt, match what it produces.

---

## 4. Running the visualizer

```bash
cd visualizer
npm install              # one time
npm run dev              # → http://localhost:5173
npm run build            # static bundle in dist/
```

Notes:

- `vite.config.js` has `server.watch.usePolling: true` because the project
  lives on a WSL-mounted Windows drive where `fs.watch()` throws `EISDIR`.
  Remove it on a normal filesystem to lower idle CPU.
- For the very first run on Windows + WSL, install dependencies *inside* WSL
  (`wsl npm install`) to avoid `EPERM`/`EISDIR` cleanup errors, then run the
  build/dev server from either side.
