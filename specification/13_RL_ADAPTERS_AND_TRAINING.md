# 13 RL Adapters and Training Plan

> Defines the RL-facing implementation contract for policy adapters, telemetry, evaluation, and training artifacts. This document complements the game specification without changing the core mechanics.

---

## Purpose

The environment is designed to train and evaluate LLM agents on cooperative long-horizon resource allocation. The RL layer must make that trainable by providing:

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
- `PROPOSE_BUDGET`
- `VOTE`
- `ABSTAIN_FROM_PROPOSAL`

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

Multiple LLM-backed ministers debate publicly, propose budgets, and vote.

Purpose:

- evaluate whether debate improves information aggregation
- test long-horizon cooperation under partial observability
- produce interpretable transcripts for storytelling

### Dictator LLM Adapter

A single LLM produces an allocation plan for the parliament.

Purpose:

- compare decentralized debate against centralized planning
- provide a useful storytelling contrast

Two variants are allowed:

- realistic dictator: receives only legally observable information
- oracle dictator: receives hidden state only for upper-bound evaluation, never as a deployable policy

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
