# Project File Structure

> Complete layout for the Nation Optimizer RL environment. Files marked with ✅ exist, ⬜ need to be created.

---

## Root

```
nation-optimizer-rl/
│
├── README.md                          ✅  Project overview and documentation
├── FILE_STRUCTURE.md                  ✅  This file
├── pyproject.toml                     ⬜  Project metadata, dependencies, entry points
├── requirements.txt                   ⬜  Pip dependencies (openenv, pydantic, fastapi, etc.)
├── Dockerfile                         ⬜  Container for OpenEnv deployment
├── openenv.yaml                       ⬜  OpenEnv environment manifest
├── .gitignore                         ⬜  Python gitignore
│
├── assets/                            ✅  Static assets
│   └── poster.png                     ✅  Project poster image
│
├── specification/                     ✅  Game design documents (14 files)
│   ├── 00_INDEX.md                    ✅  Navigation and reading guide
│   ├── 01_GAME_OVERVIEW.md            ✅  Concept, inspiration, goals
│   ├── 02_GAME_RULES_REFERENCE.md     ✅  Single-page rules reference
│   ├── 03_TURN_STRUCTURE.md           ✅  9-phase turn flow
│   ├── 04_ECONOMY_MODEL.md            ✅  Treasury, revenue, piecewise curve
│   ├── 05_VOTING_PROTOCOL.md          ✅  Voting, tie-breaking, abstention
│   ├── 06_EVENT_SYSTEM.md             ✅  Event catalog, multipliers, black swans
│   ├── 07_AGENT_ACTION_SPACE.md       ✅  Valid agent actions per phase
│   ├── 08_OBSERVATION_SPACE.md        ✅  What agents observe
│   ├── 09_REWARD_MODEL.md             ✅  Prosperity reward function
│   ├── 10_SUCCESS_CRITERIA.md         ✅  Win/loss conditions, baselines
│   ├── 11_GUARDRAILS.md               ✅  Explicit exclusions
│   ├── 12_GLOSSARY.md                 ✅  Defined terms
│   └── APPENDIX_A_EXAMPLES.md         ✅  Numerical walkthroughs
│
├── core/                              ✅  Pure game engine (no OpenEnv dependency)
│   ├── __init__.py                    ✅  Package init
│   ├── config.py                      ⬜  Constants and tunable parameters
│   ├── game.py                        ✅  Main game engine (NationGame class)
│   ├── revenue.py                     ⬜  Piecewise revenue curve function
│   ├── sector.py                      ⬜  Sector class (state, thresholds, revenue)
│   ├── treasury.py                    ⬜  Treasury manager (tax, debits, credits)
│   ├── events.py                      ⬜  Event engine (generation, application)
│   ├── productivity.py                ⬜  Persistent productivity tracker
│   ├── population.py                  ⬜  Population dynamics (birth, death, crisis)
│   ├── reward.py                      ⬜  Reward calculator (prosperity, bonuses, penalties)
│   ├── sectors.json                   ✅  Sector definitions (baselines, thresholds)
│   └── events.json                    ✅  Event catalog (multipliers, severity, narratives)
│
├── server/                            ⬜  OpenEnv server (FastAPI + WebSocket)
│   ├── __init__.py                    ⬜  Package init
│   ├── environment.py                 ⬜  OpenEnv Environment subclass (wraps core/game.py)
│   ├── models.py                      ⬜  Pydantic Action/Observation/State models
│   └── app.py                         ⬜  FastAPI application factory
│
├── agents/                            ⬜  Agent implementations
│   ├── __init__.py                    ⬜  Package init
│   ├── base_agent.py                  ⬜  Abstract base agent class
│   ├── random_agent.py                ⬜  Random baseline agent
│   ├── greedy_agent.py                ⬜  Greedy baseline agent
│   ├── conservative_agent.py          ⬜  Conservative baseline (allocates at demand)
│   ├── optimal_agent.py               ⬜  Optimal baseline (allocates at ~130% demand)
│   └── llm_agent.py                   ⬜  LLM-powered agent (HuggingFace inference)
│
├── tests/                             ⬜  Test suite
│   ├── __init__.py                    ⬜  Package init
│   ├── test_revenue.py                ⬜  Piecewise revenue curve unit tests
│   ├── test_sector.py                 ⬜  Sector threshold and state tests
│   ├── test_treasury.py               ⬜  Treasury math tests
│   ├── test_events.py                 ⬜  Event generation and application tests
│   ├── test_game.py                   ⬜  Full game loop integration tests
│   ├── test_reward.py                 ⬜  Reward calculation tests
│   └── test_environment.py            ⬜  OpenEnv API contract tests
│
└── scripts/                           ⬜  Utility scripts
    ├── run_server.py                  ⬜  Start OpenEnv server locally
    ├── run_episode.py                 ⬜  Run a single episode with chosen agents
    ├── plot_revenue_curve.py          ⬜  Visualize piecewise revenue function
    └── benchmark_baselines.py         ⬜  Run all baselines and compare metrics
```

---

## Module Dependency Graph

```
┌──────────────────────────────────────────────────────────┐
│                     scripts/                              │
│  run_server.py  run_episode.py  benchmark_baselines.py   │
└────────────┬──────────────┬──────────────────────────────┘
             │              │
             ▼              ▼
┌─────────────────┐  ┌──────────────┐
│   server/        │  │   agents/     │
│  environment.py  │  │  llm_agent   │
│  models.py       │  │  baselines   │
│  app.py          │  └──────┬───────┘
└────────┬────────┘          │
         │                   │
         ▼                   ▼
┌──────────────────────────────────┐
│            core/                  │
│                                   │
│  game.py ◄── Main orchestrator    │
│    │                              │
│    ├── revenue.py    (piecewise)  │
│    ├── sector.py     (state)      │
│    ├── treasury.py   (finances)   │
│    ├── events.py     (stochastic) │
│    ├── productivity.py (persist)  │
│    ├── population.py (dynamics)   │
│    ├── reward.py     (prosperity) │
│    └── config.py     (constants)  │
│                                   │
│  sectors.json  events.json        │
└──────────────────────────────────┘
```

---

## Key Design Principle: Separation of Concerns

```
core/game.py          ──►  Pure game logic. Zero framework dependencies.
                            Input: dict of allocations per sector
                            Output: dict with treasury, revenues, reward, done

server/environment.py ──►  Thin OpenEnv wrapper. Translates between
                            OpenEnv Action/Observation and core game dicts.

agents/*              ──►  Consume observations, produce actions.
                            No knowledge of game internals.
```

This means:
- `core/` can be tested independently with plain Python
- `server/` can be swapped for Gymnasium or any other framework
- `agents/` work through the environment API only

---

## File Descriptions

### `core/` — Pure Game Engine

| File | Responsibility |
|------|---------------|
| `config.py` | All magic numbers: `POP_0=1_000_000`, `BASELINE_TAX=100`, `PRODUCTIVITY_BOUNDS=(0.5, 2.0)`, `CRITICAL_RATIO=0.4`, `SURPLUS_RATIO=1.5`, `WASTAGE_RATIO=2.5`, `RF_MAX=1.8`, `MAX_ROUNDS=50` |
| `revenue.py` | `revenue_factor(x, critical, demand, surplus, wastage) → float or None`. The 4-segment piecewise curve. Returns `None` for critical failure. |
| `sector.py` | `Sector` class holding baseline, current demand, allocation, revenue factor, revenue. Methods: `compute_thresholds(pop, pop0, event_mult)`, `compute_revenue_factor(allocation)`, `compute_revenue(allocation, productivity)` |
| `treasury.py` | `Treasury` class. Tracks balance. Methods: `debit(amount)`, `credit(amount)`, `apply_baseline_tax()`, `is_bankrupt()` |
| `events.py` | `EventEngine` class. Loads `events.json`. Methods: `generate_events(rng) → list[Event]`, `apply_event(event, sectors)` (sets multipliers). Handles positive treasury injections. |
| `productivity.py` | `ProductivityTracker`. Persistent state [0.5, 2.0]. Method: `update(avg_revenue_factor) → float` |
| `population.py` | `PopulationTracker`. Method: `update(productivity, crisis_occurred) → int` |
| `reward.py` | `compute_reward(revenues, productivity, round_num, sectors, critical_failed) → float`. Implements the full reward formula from spec 09. |
| `game.py` | `NationGame` class. Orchestrates a full round: event → allocate → critical check → execute → revenue → surplus return → productivity/population update → reward → termination check. Single method: `step(allocations: dict[str, float]) → StepResult` |
| `sectors.json` | `{"Social": {"baseline": 60}, "Agriculture": {"baseline": 70}, ...}` |
| `events.json` | Full event catalog with multipliers, severity ranges, treasury injections, narratives |

### `server/` — OpenEnv Integration

| File | Responsibility |
|------|---------------|
| `models.py` | Pydantic models: `NationAction(Action)` with `allocations: dict[str, float]`, `NationObservation(Observation)` with treasury/revenue/events/etc., `NationState(State)` with full game state |
| `environment.py` | `NationEnvironment(MCPEnvironment)`. Wraps `NationGame`. Implements `reset()`, `step()`, `state`. Translates between Pydantic models and game dicts. Exposes MCP tools for LLM agents. |
| `app.py` | FastAPI app factory. Registers the environment, health endpoint, schema endpoint. |

### Root — Deployment Files

| File | Responsibility |
|------|---------------|
| `Dockerfile` | Python 3.11 image, installs deps, runs `app.py` on port 8000 |
| `openenv.yaml` | OpenEnv manifest: environment name, description, action/observation schemas |

### `agents/` — Agent Implementations

| File | Responsibility |
|------|---------------|
| `base_agent.py` | ABC with `act(observation) → action` and `reset()` |
| `random_agent.py` | Random allocations in [0, treasury/N] range |
| `greedy_agent.py` | Always requests max budget for own department |
| `conservative_agent.py` | Allocates exactly at demand (100%) for each sector |
| `optimal_agent.py` | Allocates at ~130% demand (profit zone sweet spot) |
| `llm_agent.py` | Formats observation as prompt, calls HuggingFace API, parses allocation response |

### `tests/`

| File | Key Tests |
|------|-----------|
| `test_revenue.py` | RF at critical=0, demand=1.0, surplus=1.8, wastage=1.0, beyond<1.0. Critical returns None. |
| `test_sector.py` | Threshold computation with population scaling and event multipliers |
| `test_treasury.py` | Debit/credit math, bankruptcy detection, baseline tax |
| `test_events.py` | Event generation distribution, multiplier application, treasury injection |
| `test_game.py` | Full episode: normal round, crisis round, critical failure, shutdown |
| `test_reward.py` | Prosperity calc, zone penalties, critical penalty=-1000 |
| `test_environment.py` | OpenEnv contract: reset→Observation, step→Observation, state→State |

---

## Implementation Order

```
Phase 1: Core Engine (no dependencies)
  1. config.py          ← constants
  2. revenue.py         ← piecewise curve
  3. sector.py          ← sector state
  4. treasury.py        ← treasury manager
  5. productivity.py    ← persistent tracker
  6. population.py      ← population dynamics
  7. events.py          ← event engine
  8. reward.py          ← reward calculator
  9. sectors.json       ← sector data
  10. events.json       ← event catalog
  11. game.py           ← orchestrator

Phase 2: Tests
  12. test_revenue.py
  13. test_game.py      ← smoke test full loop

Phase 3: OpenEnv Server
  14. models.py         ← Pydantic models
  15. environment.py    ← OpenEnv wrapper
  16. app.py            ← FastAPI server

Phase 4: Agents & Baselines
  17. random_agent.py
  18. conservative_agent.py
  19. optimal_agent.py
  20. llm_agent.py

Phase 5: Scripts & Polish
  21. run_episode.py
  22. benchmark_baselines.py
  23. plot_revenue_curve.py
```
