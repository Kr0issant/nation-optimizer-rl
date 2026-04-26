# 13 RL Adapters and Training Plan

> Defines the RL-facing implementation contract for policy adapters, telemetry, evaluation, and training artifacts. This document complements the game specification without changing the core mechanics.

---

## Purpose

The environment is designed to train and evaluate an LLM on long-horizon resource allocation through structured reasoning. The RL layer must make that trainable by providing:

- structured policy adapter interfaces
- reproducible baseline comparisons
- centralized rollout logging
- training data generation
- minimal Hugging Face TRL or Unsloth training scripts
- reward and behavior improvement evidence for judging

This document is implementation-facing. The authoritative game mechanics remain in `01` through `12`.

---

## Adapter Contract

All policies implement the same adapter interface:

```python
adapter.act(observation, valid_actions, agent_id) -> Action
```

### Inputs

- `observation`: the phase-specific observation defined in `08_OBSERVATION_SPACE.md`
- `valid_actions`: the action mask derived from `07_AGENT_ACTION_SPACE.md`
- `agent_id`: the minister identity for this adapter call

### Output

One structured action:

- `DEBATE`
- `PROPOSE_BUDGET` (proposal amounts are **discretionary**; critical minima are auto-funded and need not be proposed)
- `VOTE`

Adapters suggest actions only. The environment validates phase constraints, treasury limits, proposal ownership, vote eligibility, and termination.

---

## Required Adapter Families

### Greedy Adapter

Each minister maximizes its own departmental request and votes permissively.

Purpose:

- demonstrate tragedy-of-commons dynamics
- show treasury depletion and wastage-zone behavior
- provide an intentionally poor but interpretable baseline

### Equal-Split Adapter

Each minister requests an equal share of the visible treasury.

Purpose:

- demonstrate naive fairness
- show why equal division fails when baselines, events, and demand multipliers differ

### Conservative Adapter

Each minister requests baseline demand.

Purpose:

- provide a stable non-learning baseline
- show survival without strong prosperity growth

### Optimal-Zone Heuristic Adapter

Each minister targets the profit zone, approximately 1.3x demand when affordable.

Purpose:

- provide a strong hand-coded baseline
- anchor reward curves against the known piecewise revenue model

### Parliamentary LLM Adapter

The same underlying LLM is called multiple times with different minister role prompts to simulate debate, proposals, and voting.

Purpose:

- evaluate whether structured reasoning (debate + voting) improves long-horizon planning
- test interpretability through reasoning traces under partial observability
- produce interpretable transcripts for storytelling

**Important**: This is NOT multi-agent RL. There is one model with multiple role-play prompts. The "parliament" is cognitive scaffolding—interpretable structure wrapped around a single learner.

### Dictator LLM Adapter

The same underlying LLM receives a single central-planner prompt that directly outputs allocations for all departments.

Purpose:

- compare structured reasoning (parliamentary) against direct planning (dictator)
- provide an opaque baseline using identical model capacity
- isolate the effect of reasoning structure on performance

Two variants are allowed:

- realistic dictator: receives only legally observable information
- oracle dictator: receives hidden state only for upper-bound evaluation, never as a deployable policy

---

## Direct-Allocation Shortcut Mode

The adapter contract above mirrors the full nine-phase parliamentary cycle. The engine (`core/game.py`) additionally exposes a **direct-allocation shortcut** that collapses an entire round into a single action, bypassing debate, proposals, and voting. This mode exists strictly to make the environment compatible with vectorised RL libraries that expect a fixed-shape continuous action (PPO, SAC, A2C, TD3, etc.) and to support sanity-checking the economy in isolation from negotiation dynamics.

This shortcut is a deliberate **simplification of the action interface only**. It does not change the underlying economy, reward model, event system, or observation space. It does **not** train or evaluate parliamentary behaviour.

### Activation

`NationGame.step(action)` dispatches to direct-allocation mode when `action` is a `Mapping[str, float]` whose keys are a non-empty subset of `config.SECTOR_ORDER` and which contains **no `"type"` field**. Any other shape (single structured action dict with `type`, or a list of such dicts) is routed to the standard phase machinery.

### Action Contract

- Type: `dict[str, float]`, e.g. `{"Social": s, "Agriculture": a, "Health": h, "Education": e, "Defense": d, "Commerce": c}`.
- Keys: drawn from `SECTOR_ORDER` (the six v1 departments).
- Values: requested allocation per department, must be `>= 0`. Missing departments default to `0.0`.
- For gym-style adapters using a `Box` action space, the canonical vector form is the ordered tuple `(amount_for_sector for sector in SECTOR_ORDER)`. Wrappers MAY clip, scale, or soft-bound this vector before passing it to the engine, but MUST preserve key order.
- The mapping does not undergo proposal validation or voting: every entry is treated as an already-approved allocation against the current treasury. If the sum exceeds the treasury, individual sectors may still trip the critical-failure check after debit.

### Round Semantics

A single call to `step` performs one full round:

1. Resets the engine to Phase 1 (`EVENT_REVELATION`) if it is mid-round, regenerating events if needed.
2. Synthesises one approved proposal per department with `agent_id == department` and the supplied amount.
3. Debits the treasury by the sum of allocations.
4. Runs Phase 6 (consumption), Phase 7 (revenue), Phase 8 (surplus rollover + baseline tax) in order.
5. Runs Phase 9 (termination check) and, if the episode continues, advances to the next round.
6. Returns a `StepResult` with `info["accepted_actions"] == [{"type": "DIRECT_ALLOCATION"}]`.

Critical-failure detection still applies: any sector whose allocation is below its critical threshold for the current population terminates the episode with `termination_reason == "CRITICAL_FAILURE"`. Bankruptcy, shutdown, max-rounds, and prosperity-streak terminations are unchanged.

### Observation Contract

The observation returned is structurally identical to the standard `StepResult.observation` defined in `08_OBSERVATION_SPACE.md`, with the following invariants specific to this mode:

- `proposals` contains six synthetic approved proposals (one per department), authored by the department itself, with empty `votes` and `justification`.
- `debate_messages` is always empty.
- `votes` is always empty.
- `phase` and `phase_name` reflect the post-round phase (Phase 1 of the next round, or the terminal phase if the episode ended).
- `valid_actions` from `07_AGENT_ACTION_SPACE.md` is not meaningful here; the only valid "action" is the next allocation mapping.
- All other public fields (treasury, population, productivity, sector-level allocation/consumption/revenue/surplus, event ledger, current events, last reward, total reward) are populated identically to the parliamentary path.

### When To Use

Use the direct-allocation shortcut **only** for:

- Continuous-control RL baselines (PPO, SAC, A2C, TD3) where a six-dimensional `Box` action space is required.
- Sanity-checking the economy (four-zone revenue curve, productivity, surplus rollover, baseline tax) under a known policy.
- Generating reference upper bounds on the economic optimisation problem in isolation from negotiation.
- Smoke-testing telemetry, reward, and termination plumbing without the cost of a full nine-phase cycle.

### When NOT To Use

Do **not** use this mode for:

- The hackathon's headline research question on decentralised debate vs. central planning. That comparison must use the parliamentary interface (and, where appropriate, the dictator adapter from *Required Adapter Families*) so that observed differences are attributable to the negotiation protocol rather than the action interface.
- Training or evaluating any LLM or parliamentary-LLM adapter.
- Reporting against the baseline ranking in *Evaluation Protocol* below. Those baselines are defined over the structured `PROPOSE_BUDGET / VOTE / DEBATE` action space; direct-allocation runs are not directly comparable to them.

### Reporting Requirements

When publishing results obtained through this shortcut:

- Label them explicitly as `direct-allocation` (or `central-planner`) runs.
- Quote them in a separate table from the parliamentary baselines, never interleaved.
- State that the policy did not exercise the voting, proposal, or debate protocol.

### Guardrails (in addition to those in `11_GUARDRAILS.md` and the *Guardrails* section below)

- Direct-allocation is the only sanctioned full-round shortcut. Do not introduce additional shortcuts that bypass proposal validation, voting, or phase ordering.
- Direct-allocation policies still observe only public state; they receive no privileged information unless the run is explicitly an oracle benchmark.
- Direct-allocation episodes do not satisfy the parliamentary "reward improvement" success criterion in *Success Criteria* below; a separate, clearly labelled track is required.

---

## Telemetry Requirements

Central logging is mandatory for evaluation and training.

Each episode should emit JSONL records for:

- observations
- prompts
- model completions
- parsed actions
- validation results
- proposals
- votes
- rewards
- treasury balance
- prosperity
- productivity
- termination reason
- token usage when LLMs are used

Telemetry records are the source of truth for:

- reward plots
- baseline comparisons
- qualitative episode playback
- TRL/Unsloth training datasets

---

## Evaluation Protocol

All adapters must be evaluated on shared random seeds.

Primary metrics:

- mean episode return
- survival rounds
- critical failure rate
- bankruptcy rate
- shutdown rate
- final prosperity
- average revenue factor
- treasury stability
- productivity growth

LLM-specific metrics:

- invalid action rate
- JSON parse failure rate
- prompt tokens
- completion tokens
- debate messages per round
- proposals passed per round

Baseline comparison order:

1. random
2. greedy
3. equal split
4. conservative
5. optimal-zone heuristic
6. parliamentary LLM
7. dictator LLM
8. trained policy

---

## Training Strategy

Given limited Hugging Face credits, prioritize cheap and demonstrable training.

Recommended sequence:

1. Build the environment and deterministic baselines.
2. Collect rollout telemetry from all baseline adapters.
3. Run LLM adapters in inference mode on a small seed set.
4. Convert high-reward rollouts into supervised or preference data.
5. Train a small LoRA/QLoRA adapter with TRL or Unsloth.
6. Re-run evaluation on the same seeds and plot before/after rewards.

Full LLM RL fine-tuning is not required for the first demo. The hackathon requirement is a working training script and evidence of reward improvement.

---

## Success Criteria

The RL layer is successful when it can show:

- all baseline adapters running against the same environment contract
- centralized JSONL logs for every episode
- seeded reward comparisons
- at least one training script using TRL or Unsloth
- reward/loss plots committed under `assets/results/`
- README links to the Hugging Face Space and training evidence

---

## Guardrails

- Do not add individual rewards.
- Do not let adapters access hidden event costs unless explicitly running an oracle baseline.
- Do not allow private side-channel communication between agents.
- Do not move game-rule validation into adapters.
- Do not treat prompt text as an environment action unless it parses into the structured action schema.
- For **OpenEnv Hackathon** submissions, also satisfy the **minimum deliverables** in `specification/PROBLEM_STATEMENT/` (e.g. latest OpenEnv, TRL *or* Unsloth training script, training evidence, Space, README links). `11_GUARDRAILS.md` explains how that relates to documents `01`–`12`.
