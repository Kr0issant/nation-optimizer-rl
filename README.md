# Nation Optimizer RL

> A multi-agent reinforcement learning environment simulating cooperative parliamentary resource allocation. Inspired by the Marxist principle: *"From each according to his ability, to each according to his need."*

![Project Poster](assets/poster.png)

## Overview

This project is a **cooperative multi-agent RL environment** where LLM-powered ministers collectively manage a nation's treasury through sequential budget negotiations, voting, and debate.

- **Agents**: Ministers with distinct departmental portfolios (Health, Defense, Agriculture, Education, Commerce, Social)
- **Mechanism**: Sequential budget proposals with public voting rounds
- **Reward**: Collective prosperity (GDP per capita) — all agents succeed or fail together
- **Uncertainty**: Stochastic events with hidden costs force agents to infer needs from partial information
- **Constraint**: No debt allowed. Bankruptcy = episode failure.

## What This Model Captures

Despite its simplifications, the simulation captures five core dynamics of collective governance:

1. **Cooperation under uncertainty**
   > Can agents share limited resources when each department's true needs are hidden?

2. **Sequential negotiation**
   > How does proposal order affect outcomes? Does the first proposer capture the treasury?

3. **Collective action**
   > Can agents avoid the tragedy of the commons when everyone draws from the same pool?

4. **Forward-looking behavior**
   > Do agents save surplus for future crises, or spend everything now?

5. **Information aggregation**
   > Can parliament infer hidden states (event costs) from public debate and severity signals?

## The Core Theoretical Question

> **"Under what conditions do self-interested agents (operating under collective reward) achieve cooperative resource allocation comparable to a central planner with perfect information?"**

This is essentially asking: *Can decentralized voting approximate optimal planning?*

In economics, this connects to:
- **Hayek's Knowledge Problem**: Can dispersed information be aggregated through voting?
- **Mechanism Design**: Can rules align individual and collective incentives?
- **Computational Social Choice**: How hard is it to compute fair allocations?
- **Cooperative Game Theory**: Can the core be reached through negotiation?

## Theoretical Assumptions

The simulation makes explicit assumptions from several economic traditions:

| Tradition | Assumption | Our Implementation |
|-----------|-----------|-------------------|
| **Keynesian** | Spending drives growth | `Productivity = f(Investment)` where Investment = actual consumption |
| **Soviet Planning** | Centralized allocation | All resources flow through treasury; no private market |
| **Public Choice** | Voting determines budgets | Majority rule with rotating proposal order |
| **Neoclassical Growth** | Population affects per-capita output | `Prosperity = Output / Population` with exogenous growth |
| **Information Economics** | Uncertainty requires inference | Agents observe severity + narrative, NOT exact cost |
| **Austrian/Black Swan** | Rare extreme events disrupt equilibrium | 40% normal rounds, 1% black swan crises |
| **Marxist Distribution** | Collective reward | All agents receive identical reward |
| **Institutional Economics** | Rules shape behavior | Hard constraints (no debt, no self-voting, rotating order) |

## Specification

The complete game design is documented in the [`specification/`](specification/) folder:

| Document | Content |
|----------|---------|
| [`00_INDEX.md`](specification/00_INDEX.md) | Navigation and reading order |
| [`01_GAME_OVERVIEW.md`](specification/01_GAME_OVERVIEW.md) | Concept, inspiration, goals |
| [`02_GAME_RULES_REFERENCE.md`](specification/02_GAME_RULES_REFERENCE.md) | Single-page rules reference |
| [`03_TURN_STRUCTURE.md`](specification/03_TURN_STRUCTURE.md) | 9-phase turn flow |
| [`04_ECONOMY_MODEL.md`](specification/04_ECONOMY_MODEL.md) | Treasury, revenue, efficiency formulas |
| [`05_VOTING_PROTOCOL.md`](specification/05_VOTING_PROTOCOL.md) | Voting mechanics, tie-breaking, abstention |
| [`06_EVENT_SYSTEM.md`](specification/06_EVENT_SYSTEM.md) | Event catalog, severity, black swans |
| [`07_AGENT_ACTION_SPACE.md`](specification/07_AGENT_ACTION_SPACE.md) | Valid agent actions |
| [`08_OBSERVATION_SPACE.md`](specification/08_OBSERVATION_SPACE.md) | What agents observe |
| [`09_REWARD_MODEL.md`](specification/09_REWARD_MODEL.md) | Prosperity/GDP reward function |
| [`10_SUCCESS_CRITERIA.md`](specification/10_SUCCESS_CRITERIA.md) | Winning/losing conditions |
| [`11_GUARDRAILS.md`](specification/11_GUARDRAILS.md) | Explicit exclusions (mechanics vs hackathon deliverables) |
| [`12_GLOSSARY.md`](specification/12_GLOSSARY.md) | Defined terms |
| [`13_RL_ADAPTERS_AND_TRAINING.md`](specification/13_RL_ADAPTERS_AND_TRAINING.md) | Adapters, telemetry, evaluation, TRL/Unsloth pipeline |
| [`APPENDIX_A_EXAMPLES.md`](specification/APPENDIX_A_EXAMPLES.md) | Concrete numerical examples |

**Hackathon themes and judging (external minimum bar):** [`specification/PROBLEM_STATEMENT/`](specification/PROBLEM_STATEMENT/) — OpenEnv Apr ’26 themes, TRL/Unsloth requirement, Space, plots, and README expectations.

**Sprint plan (reconciled with the spec):** [`ImplemenationPlanRLIncluded.md`](ImplemenationPlanRLIncluded.md).

## Key Design Decisions

- **Model A: Government Budget Execution**: Treasury pays only for actual consumption, not full allocations. Unspent budget returns to treasury.
- **Rotating Proposal Order**: Departments rotate each round (`departments[t mod N]`) to prevent permanent first-mover advantage.
- **No Self-Voting**: Ministers must abstain from voting on their own proposal.
- **Investment-Driven Productivity**: Actual spending (consumption) boosts next round's productivity, not savings.
- **Revenue from Consumption**: Departments generate revenue from actual output, not budget size.
- **Population Growth**: Healthy population growth (0.5%/round) with health and crisis impacts.
- **Black Swan Distribution**: 40% normal rounds, rare crises (1% compound black swan events).
- **Government Shutdown**: If parliament fails to allocate any budget for 2 consecutive rounds, episode ends with governance collapse.

## v1 Department List

1. **Social/Municipal** — Baseline: 60
2. **Agriculture** — Baseline: 70
3. **Health** — Baseline: 90
4. **Education/R&D** — Baseline: 80
5. **Defense** — Baseline: 100
6. **Commerce** — Baseline: 75

## Getting Started

Read the specification in order:
1. [`01_GAME_OVERVIEW.md`](specification/01_GAME_OVERVIEW.md) for concept
2. [`02_GAME_RULES_REFERENCE.md`](specification/02_GAME_RULES_REFERENCE.md) for all mechanics
3. [`03_TURN_STRUCTURE.md`](specification/03_TURN_STRUCTURE.md) for game flow
4. [`APPENDIX_A_EXAMPLES.md`](specification/APPENDIX_A_EXAMPLES.md) for concrete scenarios

## Development

This project uses `uv` and top-level Python packages (`core`, `agents`, `schemas`, `telemetry`, `evaluation`, `training`).

```bash
uv sync --extra dev
uv run pytest
uv run python -m evaluation.benchmark_policies --seeds 1,2,3 --max-rounds 3
uv run --extra viz python -m evaluation.benchmark_policies --seeds 1,2,3 --max-rounds 3 --plot
```

Core game rules live in the engine layer; policy adapters consume observations and emit structured actions only. The benchmark runs the random, greedy, equal-split, conservative, and optimal-zone baselines against the same in-process `NationGame` seeds, writes `assets/results/benchmark_summary.json`, and saves plot PNGs under `assets/results/` when `--plot` is enabled. Central telemetry writes JSONL rollout records that can be reused for plots, evaluation, and training datasets.

### Run the Server / Space

The OpenEnv-compatible server wraps `core.game.NationGame` without changing game rules. It uses `openenv-core==0.2.3`, exposes the thin whole-game wrapper at `server.app:app`, and is configured for Hugging Face Space hosting through `openenv.yaml`.

```bash
uv sync --extra dev
uv run uvicorn server.app:app --host 0.0.0.0 --port 8000
```

For Docker or Space smoke tests:

```bash
docker build -t nation-optimizer-rl .
docker run --rm -p 8000:8000 nation-optimizer-rl
```

### LLM adapters

`agents.llm.ParliamentaryLLMAdapter` runs one model-backed minister per acting agent. It builds prompts from legal public observation fields, asks for exactly one JSON action, parses through the strict action parser, and logs each call as `LLM_CALL` telemetry with prompt, completion, parse outcome, parsed or fallback action, and token counts when the client reports them.

`agents.llm.DictatorLLMAdapter` uses a single central-planner prompt while preserving the same one-action adapter boundary. Because the current environment API validates per-agent actions, its `act_for_agents` shim calls the model one agent at a time instead of bypassing parliament or changing collective reward math. The default path is non-oracle; `oracle=True` is only for explicitly gated research comparisons.

Tests and CI should use mock `TextGenerationClient` implementations, so no network or `HF_TOKEN` is required. For live inference, install `huggingface_hub`, set `HF_TOKEN` and `HF_MODEL_ID`, and construct `HuggingFaceTextGenerationClient`. Training and fine-tuning are separate from these inference adapters and belong to Mega 4 under `training/`.

## Hackathon Context

This project targets the **OpenEnv Hackathon** (India 2026) expectations described in [`specification/PROBLEM_STATEMENT/`](specification/PROBLEM_STATEMENT/) (themes, judging weights, and **minimum submission** requirements). In short:

- **OpenEnv (latest):** build on the framework; use `Environment` / `MCPEnvironment`, Gym-style `reset` / `step` / `state`, client–server boundaries, and a valid **`openenv.yaml`** when the server is published.
- **Training:** a **working script** using **Hugging Face TRL** or **Unsloth** (ideally Colab-runnable) that trains **against the environment**, not only a static dataset, with **evidence** (loss and reward or clear before/after behavior, plots committed as e.g. PNG in-repo).
- **Storytelling:** mini-blog on Hugging Face or a YouTube video **under two minutes** (or short deck); link everything from this README; host the **Space** and submit the Space URL.
- **Judging (overview):** environment innovation, storytelling, **showing improvement in rewards** (curves, baselines), and **reward + training pipeline** coherence.

**Collective reward** and mechanics guardrails are unchanged; see [`11_GUARDRAILS.md`](specification/11_GUARDRAILS.md) for how **mechanics specs (01–12)** relate to these **deliverable** requirements.

## License

MIT
