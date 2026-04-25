# Implementation plan (reconciled with the specification)

**Purpose:** This file is a **sprint-style team plan** (originally a 30-hour, three-person split). It is **reconciled** with the authoritative game design in [`specification/`](specification/) and the current engine in [`core/game.py`](core/game.py). If anything here disagrees with `specification/` or `core/`, **those win**.

**Hackathon bar:** OpenEnv submission, TRL *or* Unsloth training script, plots, Space, and README materials are defined in [`specification/PROBLEM_STATEMENT/`](specification/PROBLEM_STATEMENT/) (see the Apr ’26 OpenEnv themes and judging criteria document). This plan aligns with that deliverables list.

---

## How this differs from the first draft of this file

| Earlier draft (superseded) | Current design |
|----------------------------|----------------|
| `NationGame.step(allocations: dict)` as the main API | Phased `NationGame` with **9 phases per round**; ministers emit **structured actions** (debate, propose budget, vote, abstain) per [`07_AGENT_ACTION_SPACE.md`](specification/07_AGENT_ACTION_SPACE.md). |
| Softmax over six raw floats, then `game.step(allocation_dict)` | Budget execution and revenue follow **proposals, voting, and** [`04_ECONOMY_MODEL.md`](specification/04_ECONOMY_MODEL.md). There is **no** softmax “bid vector → allocation” in the core loop. |
| Two-phase “debate then vote” as the only turn shape | **Public debate + proposals + voting** are embedded in the 9-phase turn; see [`03_TURN_STRUCTURE.md`](specification/03_TURN_STRUCTURE.md). |
| “Curriculum bailout” to ignore critical failure and inject cash | **Not** in the v1 spec: critical failure and bankruptcy are hard stops per [`10_SUCCESS_CRITERIA.md`](specification/10_SUCCESS_CRITERIA.md). Do not add bailouts in `server/` without a spec change. |
| Example sector names (e.g. “Military”, “Healthcare”) in snippets | v1 departments are fixed in the spec and data (e.g. Social, Agriculture, Health, Education, Defense, Commerce). |
| PPO as the named training path | **TRL or Unsloth** is the hackathon **minimum**; PPO (or other algorithms) is an **optional** training choice, implemented in `training/`, not in `core/`. |

---

## Constraint and architecture (unchanged in spirit)

- **Constraint:** Small team, short clock.
- **Architecture:** Deterministic **Python core** (`core/`, no OpenEnv/LLM imports), **schemas** for actions/observations/rewards, **adapters** in `agents/`, **OpenEnv**-compatible **server** layer when wired, **TRL/Unsloth** for demonstrable training per problem statement.
- **Collective reward** and **no individual rewards** are unchanged; see [`11_GUARDRAILS.md`](specification/11_GUARDRAILS.md).

---

## Phase 1 — Core engine (the math and rules)

**Goal:** The engine runs **offline** with the phased loop, treasury, revenue, events, and termination.

- **Data:** [`core/sectors.json`](core/sectors.json), [`core/events.json`](core/events.json) — follow the spec’s event and sector semantics, not ad-hoc JSON shapes from old examples.
- **Math:** [`core/revenue.py`](core/revenue.py), [`core/treasury.py`](core/treasury.py), productivity, population — match [`04_ECONOMY_MODEL.md`](specification/04_ECONOMY_MODEL.md) and related docs.
- **Orchestrator:** [`core/game.py`](core/game.py) `NationGame` — phases, proposals, voting resolution, then execution and reward.

**Validation:** Unit tests and integration tests under `tests/`; no LLM or OpenEnv required.

---

## Phase 2 — OpenEnv, server, and baselines

**Goal:** Expose the core through a **thin** `server/` wrapper (Gym-style / OpenEnv contract), **Pydantic** (or shared schema) I/O, and **rule-based** baselines per [`13_RL_ADAPTERS_AND_TRAINING.md`](specification/13_RL_ADAPTERS_AND_TRAINING.md).

- **Not in scope here:** Converting free-form model outputs into a softmax over departments. Adapters must output **valid structured actions**; the **environment** validates and advances phases.
- **Baselines:** greedy, equal-split, conservative, optimal-zone, random (as listed in `13`); use these to check stability and metrics before LLM training.

**Validation:** Smoke episodes, seeded benchmarks, treasury and metrics in range.

---

## Phase 3 — LLM adapters and training script

**Goal:** **Parliamentary** and optional **dictator** LLM flows that call a text client, parse JSON into the action schema, and log telemetry; a **TRL or Unsloth** training entrypoint that trains against **rollouts from the real environment** (not a static dataset as the only story).

- **Debate and voting:** Map to the existing phases; reuse [`agents/prompts.py`](agents/prompts.py) and strict parsing in [`agents/action_parser.py`](agents/action_parser.py).
- **Training:** Align with the hackathon doc: show **loss and reward (or policy improvement) evidence**, baselines vs trained, plots under `assets/results/` and links in the README. Algorithm choice (e.g. PPO vs supervised LoRA) stays in **implementation**, but TRL/Unsloth must be satisfied for submission.

**Validation:** Parse failure rates down; one real run committed as evidence for judges.

---

## Phase 4 — Integration, HF Space, and story

**Goal:** `openenv.yaml`, hosted Space, README links (blog/short video per criteria), and a clear “before/after” or baseline comparison.

- **Client/server separation:** Clients do not import server internals; follow OpenEnv expectations from the problem statement.
- **No** reward-hacking shortcuts that contradict [`11_GUARDRAILS.md`](specification/11_GUARDRAILS.md).

---

## File name

The filename `ImplemenationPlanRLIncluded.md` is kept to avoid breaking existing links; fix the typo if you rename it repo-wide.
