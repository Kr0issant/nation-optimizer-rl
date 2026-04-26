# Nation Optimizer RL

> A long-horizon planning environment where an LLM learns centralized resource allocation through structured parliamentary reasoning. Inspired by: *"From each according to his ability, to each according to his need."*

![Project Poster](assets/poster.png)

## What This Is

This is **not** a multi-agent game. It is a **centralized planning environment** where a single LLM manages a national economy over a 50-round (12.5-year) horizon. Every decision — budget proposals, votes, debate messages — is made by the same underlying model.

The parliamentary mechanics (debate → proposals → voting) are **cognitive scaffolding**: they force the model to decompose a complex allocation problem into sequential, publicly-justified steps. This makes the planning process **interpretable by design** — every budget decision is accompanied by a natural-language rationale.

We compare two reasoning modes with the same model:
- **Parliamentary**: Model reasons through debate, proposals, and votes before allocating
- **Dictator**: Model outputs allocations directly

The research question: *Does forced deliberative structure improve long-horizon planning quality?*

## Hackathon Themes

| Theme | Alignment |
|-------|-----------|
| **#2 — Long-Horizon Planning** | 50 rounds × 9 phases = 450 steps per episode. Sparse, delayed rewards. Credit assignment over 12.5 years. |
| **#3.1 — World Modeling** | Coupled dynamical system: treasury, productivity, population, stochastic events. Model must infer hidden costs from partial signals. |

## The Core Problem

Managing a national economy requires:
- **Long-horizon credit assignment**: Which Round 3 debate message caused the prosperity in Round 47?
- **Reasoning under uncertainty**: Events have hidden costs; the model observes severity + narrative, not exact impact
- **Coupled dynamical state**: Treasury, productivity, and population interact across rounds
- **Interpretability**: Every allocation decision must be explainable, not just optimal

Most LLM planning work uses chain-of-thought prompting. This is different — the environment **imposes** a deliberative structure. The model cannot skip debate or vote arbitrarily; it must engage the full parliamentary cycle before committing resources.

## What This Model Captures

1. **Long-horizon planning under uncertainty**
   > Can an LLM sustain a nation's economy over 12.5 years when events are stochastic and costs are hidden?

2. **Structured reasoning as interpretability**
   > Does forcing the model to debate, justify, and vote improve planning quality — or just slow it down?

3. **Credit assignment over 50 rounds**
   > Can the model learn which early-round decisions caused late-round prosperity or bankruptcy?

4. **State tracking under partial observability**
   > Can the model infer hidden event costs from public severity signals and historical patterns?

5. **Recovery from suboptimal early decisions**
   > If the treasury is depleted in Round 10, can the model adapt and recover by Round 30?

## Bounded Rationality and Generalization

The national economy is a **testbed, not the product**. The simplified model deliberately abstracts away quant-level market dynamics in favor of isolating one variable: **whether forced deliberative structure improves planning quality**.

The real claim is broader. Any resource allocation problem with:
- Competing priorities (departments, teams, divisions)
- Limited resources (finite treasury, budget, compute)
- Uncertainty (hidden events, noisy signals)
- Collective reward (shared success metric)

...is governed by the same structure. Councils, corporate planning committees, grant review boards, compute schedulers — all face this problem. The parliamentary cycle (debate → propose → vote) is a domain-agnostic reasoning protocol for such problems.

The simplified economy makes the hypothesis **testable and falsifiable**: if parliamentary reasoning outperforms direct allocation in this clean setting, the principle likely generalizes. If it doesn't, the deliberative structure is not the mechanism. Either result is publishable.

This is bounded rationality, not quant modeling: we accept that the model is not a real economy, and we use that simplicity to isolate the reasoning variable and attribute causality cleanly.

## Environment Architecture

The system comprises:

- **RL Environment** (Meta OpenEnv compatible): 9-phase game loop encoding treasury, revenue, productivity, population
- **LLM Policy** (Hugging Face inference): Single model generates all actions — debate, proposals, votes
- **Event Engine**: Stochastic events with hidden cost impact, observable severity
- **Treasury Controller**: Revenue collection, allocation execution, surplus tracking
- **Parliamentary Arbiter**: Proposal validation, voting rounds, retry logic with fallback allocations
- **Prosperity Calculator**: GDP per capita reward signal at each step
- **GRPO Training Pipeline**: TRL `GRPOTrainer` + LoRA fine-tuning on top of `Qwen2.5-0.5B-Instruct`

## Key Design Decisions

- **Auto-Funded Critical Minimums**: Every department receives `Critical_d = Demand_d × 0.4` automatically. Proposals are **discretionary** — ministers ask for additional funding above the survival floor.
- **Piecewise Revenue Model**: Revenue factor varies with allocation relative to (critical, demand, surplus, wastage). Profit zone is (demand → surplus); below critical = zero revenue.
- **Rotating Proposal Order**: Departments rotate each round to prevent permanent first-mover advantage.
- **Retry-Based Proposals**: Rejected proposals get up to 2 retry rounds before receiving baseline demand as fallback.
- **Investment-Driven Productivity**: Actual consumption (not allocation) boosts next round's productivity.
- **No Debt**: Treasury cannot go negative. Bankruptcy triggers episode termination.

## v1 Department Baselines

| Department | Baseline Need | Critical (40%) | Demand |
|------------|-------------|----------------|--------|
| Social/Municipal | 60 | 24 | 60 |
| Agriculture | 70 | 28 | 70 |
| Health | 90 | 36 | 90 |
| Education/R&D | 80 | 32 | 80 |
| Defense | 100 | 40 | 100 |
| Commerce | 75 | 30 | 75 |

## Getting Started

```bash
git clone https://github.com/Kr0issant/nation-optimizer-rl.git
cd nation-optimizer-rl
uv sync --extra dev --extra viz --extra training
```

### Run Benchmarks

Compare rule-based policies (Greedy, Conservative, OptimalZone) against shared seeds:

```bash
uv run python scripts/benchmark_baselines.py --adapter optimal-zone --episodes 10
```

### Visualize the Reward Landscape

See how the RL reward function scores different budget allocations:

```bash
uv run python scripts/benchmark_rewards.py
```

### Run LLM Ministers

```bash
# Set HF_TOKEN and HF_MODEL_ID in .env
uv run python scripts/llm_test_run.py
```

### Run the Server

```bash
uv run uvicorn server.app:app --host 0.0.0.0 --port 8000
```

## Trained Policy (GRPO)

The policy is fine-tuned with TRL's `GRPOTrainer` on top of `Qwen/Qwen2.5-0.5B-Instruct` using LoRA. Prompts are collected from `OptimalZoneAdapter` rollouts — the same prompt template drives both training and inference. Only Phase 3 (PROPOSAL) and Phase 4 (VOTING) turns receive reward signals; debate is inference-only.

The reward function ([`training/reward_fn.py`](training/reward_fn.py)) is dense and grounded in the engine's own revenue model:
- Proposals scored against sector (critical, demand, surplus) thresholds
- Votes scored by the revenue factor of the proposed allocation
- Parse failures and illegal actions penalised explicitly

- **Trained LoRA:** [`nation-optimizer/nation-parliamentary-grpo-lora`](https://huggingface.co/nation-optimizer/nation-parliamentary-grpo-lora)
- **Prompt dataset:** [`nation-optimizer/nation-parliamentary-prompts`](https://huggingface.co/datasets/nation-optimizer/nation-parliamentary-prompts)
- **Training curves:** [`nation-optimizer/grpo-parliamentary`](https://huggingface.co/spaces/nation-optimizer/grpo-parliamentary) (loss + mean reward per step)

### Reproduce the Run

```bash
# Collect prompts from OptimalZone rollouts
uv run python -m scripts.collect_grpo_prompts \
    --seeds 50 --max-rounds 12 \
    --output assets/datasets/grpo_prompts.jsonl \
    --push-to-hub nation-optimizer/nation-parliamentary-prompts

# Train GRPO + LoRA (~5 on a10g-small)
hf jobs uv run --flavor a10g-small --secrets HF_TOKEN \
    training/train_grpo.py \
    --dataset-id nation-optimizer/nation-parliamentary-prompts \
    --hub-model-id nation-optimizer/nation-parliamentary-grpo-lora

# Smoke test locally
uv run --extra training python training/train_grpo.py --smoke \
    --dataset-id nation-optimizer/nation-parliamentary-prompts
```

### Before-vs-After Evidence

| File | Content |
|------|---------|
| `policy_comparison.png` | Mean episode return per policy (trained LoRA vs baselines) |
| `survival_rounds.png` | Distribution of rounds survived per policy |
| `reward_landscape.png` | RL training signal (revenue factor vs reward) |
| `benchmark_summary.json` | Raw per-episode metrics for every policy |

![Policy comparison](assets/results/policy_comparison.png)
![Survival distribution](assets/results/survival_rounds.png)
![Reward Landscape](assets/results/reward_landscape.png)

## Theoretical Assumptions

| Tradition | Assumption | Our Implementation |
|-----------|-----------|-------------------|
| **Keynesian** | Spending drives growth | `Productivity = f(Investment)` |
| **Soviet Planning** | Centralized allocation | Single planner controls all resources |
| **Explainable AI** | Interpretability improves trust | All allocations justified in natural language |
| **Information Economics** | Uncertainty requires inference | Hidden event costs, observable severity |
| **Neoclassical Growth** | Population affects per-capita output | `Prosperity = Output / Population` |

## Specification

Full game design in [`specification/`](specification/):

| Document | Content |
|----------|---------|
| [`00_INDEX.md`](specification/00_INDEX.md) | Navigation and reading order |
| [`01_GAME_OVERVIEW.md`](specification/01_GAME_OVERVIEW.md) | Concept, inspiration, goals |
| [`02_GAME_RULES_REFERENCE.md`](specification/02_GAME_RULES_REFERENCE.md) | Single-page rules reference |
| [`03_TURN_STRUCTURE.md`](specification/03_TURN_STRUCTURE.md) | 9-phase turn flow |
| [`04_ECONOMY_MODEL.md`](specification/04_ECONOMY_MODEL.md) | Treasury, revenue, efficiency formulas |
| [`05_VOTING_PROTOCOL.md`](specification/05_VOTING_PROTOCOL.md) | Voting mechanics, retry, fallback |
| [`06_EVENT_SYSTEM.md`](specification/06_EVENT_SYSTEM.md) | Event catalog, severity, black swans |
| [`07_AGENT_ACTION_SPACE.md`](specification/07_AGENT_ACTION_SPACE.md) | Valid agent actions |
| [`08_OBSERVATION_SPACE.md`](specification/08_OBSERVATION_SPACE.md) | What agents observe |
| [`09_REWARD_MODEL.md`](specification/09_REWARD_MODEL.md) | Prosperity/GDP reward function |
| [`10_SUCCESS_CRITERIA.md`](specification/10_SUCCESS_CRITERIA.md) | Winning/losing conditions |
| [`11_GUARDRAILS.md`](specification/11_GUARDRAILS.md) | Explicit exclusions |
| [`12_GLOSSARY.md`](specification/12_GLOSSARY.md) | Defined terms |
| [`13_RL_ADAPTERS_AND_TRAINING.md`](specification/13_RL_ADAPTERS_AND_TRAINING.md) | Adapters, TRL pipeline, telemetry |
| [`APPENDIX_A_EXAMPLES.md`](specification/APPENDIX_A_EXAMPLES.md) | Concrete numerical examples |

## Live Demo

**Hugging Face Space**: https://huggingface.co/spaces/ascentftw/nation_optimizer

## Hackathon Context

Built for the **Apr '26 OpenEnv Hackathon** (Meta × Hugging Face):

- **OpenEnv (latest)**: `Environment` / `MCPEnvironment`, Gym-style `reset` / `step` / `state`, valid `openenv.yaml`
- **Training**: TRL GRPO + LoRA fine-tuning on `Qwen2.5-0.5B-Instruct`; evidence of reward improvement
- **Storytelling**: Mini-blog on HuggingFace or <2 min video; Space hosted and URL submitted
- **Judging**: 40% environment innovation, 30% storytelling, 20% reward improvement evidence, 10% pipeline coherence

## License

MIT
