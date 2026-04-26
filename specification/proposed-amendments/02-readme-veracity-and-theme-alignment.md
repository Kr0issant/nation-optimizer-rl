# Proposed Amendment — README Veracity & Problem Statement Alignment

> Status: **Under deliberation**  
> Scope: README.md, specification/01_GAME_OVERVIEW.md  
> Impact: HIGH — affects hackathon judging (Storytelling 30%, Innovation 40%)

---

## 1. Problem Statement

The current README and Game Overview misrepresent the project's technical architecture. They frame it as a **"cooperative multi-agent RL environment"** where independently learning agents negotiate, vote, and cooperate. This is **not accurate** given the actual implementation and training setup.

### What the README says (current)

> "A multi-agent reinforcement learning environment simulating cooperative parliamentary resource allocation."

> "This project is a cooperative multi-agent RL environment where LLM-powered ministers collectively manage a nation's treasury through sequential budget negotiations, voting, and debate."

> "Theoretical Question: Under what conditions do self-interested agents (operating under collective reward) achieve cooperative resource allocation comparable to a central planner with perfect information?"

### What the code actually does

- **`training/train_trl.py`**: Single Q-learner placeholder (not multi-agent)
- **`agents/llm/dictator.py`**: Single model called once per agent, but no independent optimization
- **`agents/llm/parliamentary.py`**: Same model, different prompt wrapper
- **`agents/base.py`**: `PolicyAdapter` returns one action per call — the same underlying policy is reused for all agents
- **`core/game.py`**: `EpisodeReward` is a single scalar, not per-agent
- **`specification/13_RL_ADAPTERS_AND_TRAINING.md:213`**: "Do not add individual rewards" (guardrail)

**Verdict**: There is **one policy**, trained on a **single collective reward**, that outputs actions for all agents. The "ministers" are role-play personas, not independently learning agents. This is **centralized planning with a parliamentary narrative wrapper**, not multi-agent RL.

---

## 2. Why This Matters for the Hackathon

The hackathon judging criteria include:

| Criterion | Weight | Relevance |
|---|---|---|
| **Environment Innovation** | 40% | A false multi-agent claim hurts credibility if judges dig into the code |
| **Storytelling** | 30% | Misleading framing undermines trust; honest framing is more compelling |
| **Reward & Training Pipeline** | 10% | Judges will inspect training scripts; a single-learner setup contradicts "multi-agent" |

If judges read the README, then open `training/train_trl.py` (single learner) and `agents/llm/dictator.py` (single model shim), the mismatch is obvious. The storytelling score will suffer.

---

## 3. The Honest Story (Which Is Actually Better)

The project **does not need** the multi-agent framing to be impressive. The honest story is stronger:

### What This Actually Is

> A **centralized planning environment** where a single LLM learns long-horizon resource allocation through **structured, interpretable reasoning**. The parliamentary debate and voting mechanics serve as **cognitive scaffolding** — they force the model to decompose a complex allocation problem into sequential, explainable steps rather than emitting a raw allocation vector.

### Why This Is Interesting

1. **Long-horizon planning** (50 rounds × 9 phases = 450 steps per episode)
   - Sparse, delayed rewards (prosperity only materializes over many rounds)
   - Credit assignment is hard: which debate message in Round 3 caused prosperity in Round 40?
   - Fits **Hackathon Theme #2**: "(Super) Long-Horizon Planning & Instruction Following"

2. **Interpretable reasoning via role-play**
   - The model must generate public debate messages, budget justifications, and votes
   - Every decision is observable and auditable (unlike a black-box central planner)
   - This is **Explainable RL** — a genuine research gap

3. **World modeling under uncertainty**
   - Events have hidden costs; the model must infer impact from severity + narrative
   - Treasury, productivity, and population are coupled dynamical systems
   - Fits **Hackathon Theme #3.1**: "Professional Tasks / Economic simulations with feedback"

4. **Comparison architecture**
   - `Parliamentary` mode: model reasons through debate → proposals → votes (interpretable)
   - `Dictator` mode: model outputs allocations directly (opaque)
   - Both use the same underlying model; the difference is **reasoning structure**
   - Research question: *Does parliamentary reasoning improve planning performance over direct allocation?*

---

## 4. Theme Alignment

### Theme #1 — Multi-Agent Interactions

**Claim**: "Agents cooperate through debate and voting."

**Reality**: One model generates all debate messages and votes. There is no actual interaction between independent agents.

**Verdict**: Weak fit. Do not lead with this theme.

### Theme #2 — Long-Horizon Planning & Instruction Following

**Claim**: "Strategic resource management over 50 rounds with sparse rewards."

**Reality**: Exactly true. The model must plan 12.5 years ahead, track treasury state, and recover from early mistakes.

**Verdict**: **Strong fit**. This should be the primary theme.

### Theme #3.1 — World Modeling / Professional Tasks

**Claim**: "Economic simulation with feedback loops."

**Reality**: True. Treasury, productivity, population, and events form a coupled dynamical system. The model must maintain consistent internal state.

**Verdict**: **Strong fit**. Secondary theme.

### Theme #5 — Wild Card

**Claim**: "Explainable planning via parliamentary reasoning."

**Reality**: Novel and defensible. No existing environment forces LLMs to justify allocations through structured debate before committing resources.

**Verdict**: **Strong fit** if framed as interpretability research.

---

## 5. Proposed README Rewrite

### Top-Level Pitch

```markdown
# Nation Optimizer RL

> A long-horizon planning environment where LLMs learn centralized resource allocation 
> through structured parliamentary reasoning. Inspired by: *"From each according to his ability, 
> to each according to his need."*

## What This Is

This is **not** a multi-agent game. It is a **single-agent planning environment** with a 
parliamentary narrative wrapper. One LLM plays all ministers, but the learning objective is 
centralized: maximize collective prosperity over a 50-round (12.5-year) horizon.

The parliamentary mechanics (debate, proposals, voting) are **cognitive scaffolding**. 
They force the model to:
1. Articulate reasoning publicly (debate)
2. Justify specific allocations (proposals)
3. Evaluate tradeoffs explicitly (voting)

This makes the planning process **interpretable by design** — every budget decision is 
accompanied by a natural-language rationale.

## Hackathon Theme Alignment

- **Primary**: Theme #2 — Long-Horizon Planning & Instruction Following
  - 50 rounds × 9 phases = 450 steps per episode
  - Sparse, delayed rewards (prosperity accumulates gradually)
  - Recovery from early mistakes is possible and necessary

- **Secondary**: Theme #3.1 — World Modeling (Professional Tasks)
  - Coupled dynamical system: treasury, productivity, population, stochastic events
  - Model must infer hidden event costs from partial observations
  - Economic simulation with realistic feedback loops

## The Core Research Question

> **"Can structured reasoning (parliamentary debate + voting) improve long-horizon 
> resource allocation compared to direct central planning?"**

We compare two modes:
- **Parliamentary**: Model reasons through debate → proposals → votes (interpretable)
- **Dictator**: Model emits allocations directly (opaque baseline)

Both use the same underlying LLM. The only difference is the **reasoning structure** 
imposed by the environment.
```

### What This Model Captures

```markdown
## What This Model Captures

1. **Long-horizon planning under uncertainty**
   > Can an LLM sustain a nation's economy over 12.5 years when events are stochastic 
   > and costs are hidden?

2. **Structured reasoning as interpretability**
   > Does forcing the model to debate and vote improve planning quality, or just 
   > slow it down?

3. **Credit assignment over 50 rounds**
   > Can the model learn which early-round decisions caused late-round prosperity 
   > or bankruptcy?

4. **State tracking under partial observability**
   > Can the model infer hidden event costs from public severity signals and 
   > historical patterns?

5. **Recovery from suboptimal early decisions**
   > If the treasury is depleted in Round 10, can the model adapt and recover 
   > by Round 30?
```

### Theoretical Assumptions (Updated)

```markdown
## Theoretical Assumptions

| Tradition | Assumption | Our Implementation |
|-----------|-----------|-------------------|
| **Keynesian** | Spending drives growth | `Productivity = f(Investment)` |
| **Soviet Planning** | Centralized allocation | Single planner controls all resources |
| **Public Choice** | Deliberation improves decisions | Debate phase is mandatory reasoning step |
| **Neoclassical Growth** | Population affects per-capita output | `Prosperity = Output / Population` |
| **Information Economics** | Uncertainty requires inference | Hidden event costs, observable severity |
| **Explainable AI** | Interpretability improves trust | All allocations justified in natural language |
| **Marxist Distribution** | Collective reward | Single prosperity signal for all departments |
```

### Adapter Descriptions (Updated)

```markdown
### LLM Adapters

`agents.llm.ParliamentaryLLMAdapter` runs the same model multiple times per round 
(once per minister), with per-role prompts. The model generates debate messages, 
proposals, and votes as structured JSON. All reasoning is logged and observable.

`agents.llm.DictatorLLMAdapter` uses the same model but with a central-planner prompt. 
It bypasses debate and voting, emitting allocations directly. This serves as an 
opaque baseline for comparison.

The default path is non-oracle; `oracle=True` reveals hidden event costs and is 
reserved for upper-bound research comparisons only.
```

### Hackathon Context (Updated)

```markdown
## Hackathon Context

Built for the Apr '26 OpenEnv Hackathon (Meta + Hugging Face).

- **Framework**: Meta's OpenEnv for environment definition
- **Inference**: Hugging Face for LLM policy execution
- **Training**: Hugging Face TRL / Unsloth for reward-based fine-tuning
- **Themes**: #2 Long-Horizon Planning, #3.1 World Modeling
- **Innovation**: Explainable planning via structured parliamentary reasoning
```

---

## 6. What Changes in the Specification

The following spec documents contain "multi-agent" framing that should be updated:

| Document | Lines | Current Claim | Proposed Change |
|---|---|---|---|
| `01_GAME_OVERVIEW.md:5` | "cooperative multi-agent simulation" | "centralized planning simulation with parliamentary narrative" |
| `01_GAME_OVERVIEW.md:27` | "Train cooperative behavior in LLM agents" | "Train long-horizon planning through structured reasoning" |
| `01_GAME_OVERVIEW.md:30` | "Benchmark multi-agent cooperation" | "Benchmark structured reasoning against direct planning" |
| `01_GAME_OVERVIEW.md:40` | "Multi-agent RL researchers" | "LLM reasoning and planning researchers" |
| `README.md:9` | "cooperative multi-agent RL environment" | "centralized planning environment with parliamentary reasoning" |
| `README.md:36` | "self-interested agents" question | "structured reasoning vs. direct planning" question |
| `README.md:43` | "Hayek's Knowledge Problem" | Remove or reframe (not applicable to single planner) |
| `README.md:44` | "Mechanism Design" | Remove or reframe |
| `README.md:45` | "Computational Social Choice" | Remove or reframe |
| `README.md:46` | "Cooperative Game Theory" | Remove or reframe |

---

## 7. What Stays the Same

Everything else in the README is accurate and should be preserved:

- Mechanics (9 phases, revenue model, event system)
- Department list and baselines
- Getting started instructions
- Development setup
- License

The game is genuinely interesting. The only problem is the framing.

---

## 8. Implementation

| File | Action |
|---|---|
| `README.md` | Rewrite top-level pitch, themes, research question, adapter descriptions |
| `specification/01_GAME_OVERVIEW.md` | Remove "multi-agent" claims; reframe as centralized planning with interpretable reasoning |
| `specification/13_RL_ADAPTERS_AND_TRAINING.md` | Clarify that adapters are prompt wrappers, not independent agents |

**Effort**: Low (~1 hour of editing)
**Risk**: Minimal — only framing changes, no code changes

---

*This amendment is a living document. The core insight: honesty about the architecture produces a stronger, more defensible pitch than inflated multi-agent claims.*
