# Guardrails — Explicit Exclusions and Anti-Patterns

This document defines hard constraints that MUST NOT be violated during implementation or gameplay. Each guardrail exists to prevent specific failure modes discovered during design review.

---

## Scope Guardrails

- **Game mechanics documents (01–12) do not mandate a training algorithm**
  - Why: Documents `01` through `12` define rules, observations, rewards, and termination so any training approach can target the same Markov game. They intentionally avoid fixing PPO vs GRPO vs SFT, hyperparameters, or model choice.

- **Hackathon submission requirements are defined outside 01–12**
  - The authoritative **OpenEnv Hackathon** minimum bar (e.g. latest OpenEnv, a **working training script using Hugging Face TRL or Unsloth**, evidence of training such as loss/reward plots, Space hosting, README links) is given in `specification/PROBLEM_STATEMENT/` (see the Apr ’26 themes and judging criteria document). That is a **deliverables** contract, not a change to in-universe game rules.

- **`13_RL_ADAPTERS_AND_TRAINING.md` is the in-repo training and evaluation contract**
  - Why: It complements mechanics: adapters, telemetry, benchmarks, and the expected TRL/Unsloth-shaped pipeline without rewriting `02`–`10`. Implementations should satisfy both the mechanics specs and `13`, and meet the external hackathon checklist where the project is submitted.

- **NO prompt engineering or LLM jailbreak handling in mechanics documents (01–12)**
  - Why: Prompt injection attacks, system prompt extraction, or adversarial LLM behavior are implementation concerns. The specification defines the environment interface and game rules, not how to secure language model endpoints.

- **NO coalition mechanics or inter-ministry private communication**
  - Why: Private messaging between ministers introduces coalition theory complexity that explodes the state space. All debate MUST be public to all agents. This keeps the game interpretable and prevents covert alliance formation that would violate the cooperative paradigm.

- **NO dynastic changes mid-episode**
  - Why: The ministry count (4, 6, 8, etc.) is fixed at episode start. Allowing mid-episode addition or removal of ministries creates checkpointing complexity and invalidates any learning progress tracked over time.

- **NO individual reward signals**
  - Why: Every agent receives the same collective prosperity score. Individual rewards introduce zero-sum competition incentives that corrupt the cooperative resource allocation paradigm this environment is designed to study.

---

## Mechanic Guardrails

- **NO debt or borrowing of any kind**
  - Why: The treasury cannot go negative under any circumstance. If a proposed allocation exceeds available treasury, that proposal fails and the treasury remains at its current level. Loan mechanics, credit, deferred payment, or any form of negative treasury state are explicitly forbidden.

- **NO secret ballots or anonymous voting**
  - Why: All votes are public and visible to every agent in the environment. Secret ballots would hide information that agents need to learn cooperative behavior. Each agent must see who voted what to enable democratic accountability.

- **NO agent removal or ministerial bankruptcy mid-episode**
  - Why: When the treasury reaches zero or below, the episode ends immediately. There is no mechanism for removing a minister, absorbing their department, or continuing with fewer ministers. This simplifies termination conditions.

- **NO hidden information beyond exact event costs**
  - Why: Agents see event narratives and severity levels. Agents do NOT see exact cost values until after the allocation round resolves. This asymmetry is intentional. No other hidden state is permitted. Every other game variable is fully observable.

- **Maximum 2 events per round**
  - Why: More than 2 events per round creates planning complexity that exceeds the hackathon time budget. Events are stochastic shocks that disrupt planning. With more than 2 per round, agents cannot meaningfully respond and the game becomes random luck rather than strategic coordination.

- **NO dynamic event cost inference beyond narrative + severity**
  - Why: Agents receive event narrative text and severity level (1-5 scale). Agents do NOT receive any additional hints, cost probability distributions, or inference clues. The environment provides sufficient information for learning but not exact prediction.

- **NO referendum mechanics**
  - Why: All decisions follow the defined proposal-voting-execution cycle. There are no direct democracy mechanisms, emergency decrees, or bypassing of the standard voting protocol regardless of event severity.

---

## Implementation Guardrails

- **NO inter-process communication channels between agents**
  - Why: Every agent communicates ONLY through the environment interface. Agents do not have direct network sockets, shared files, or any side-channel communication. All messages pass through the central environment for observability.

- **NO shared state beyond the central treasury and event ledger**
  - Why: Each minister has independent department state (budget, productivity, surplus). Cross-department state sharing creates coupling that complicates the model. Only the treasury and global event ledger are shared.

- **NO reward hacking through treasury arbitrage**
  - Why: The reward function measures collective prosperity per capita. If ministers collude to manipulate treasury flows for reward optimization rather than genuine productivity, that represents reward hacking. The environment monitors for anomalous treasury patterns.

- **NO modification of agent action outcomes after execution**
  - Why: Once a proposal passes voting and enters execution, the outcome is final. There is no reconsideration, appeal, or veto after execution. This prevents strategic voting where agents approve proposals with no intention of accepting consequences.

- **NO event cost subsidies or hidden transfers**
  - Why: Event costs are deducted from the treasury directly. There are no hidden subsidies, no departmental cross-subsidies for event costs, and no emergency reserves that activate before treasury depletion.

---

## AI Slop Patterns to Avoid

This section documents anti-patterns that produce vague, underspecified, or unimplementable specifications. Every specification document MUST avoid these patterns.

- **Vague requirements that permit multiple interpretations**
  - Example: "agents should coordinate reasonably"
  - Why: "Reasonably" is not a valid specification term. Every mechanic needs concrete definitions. If two independent readers produce different implementations, the specification has failed.

- **Underspecified action spaces**
  - Example: "agents can take appropriate actions"
  - Why: Actions must be enumerated completely. If an agent can propose budgets, vote, and debate, then those are the only valid actions. "Appropriate actions" implies there are inappropriate ones not defined, which creates ambiguity.

- **Invisible state that affects outcomes without being documented**
  - Example: "the environment handles edge cases appropriately"
  - Why: Edge cases are not "handled appropriately" — they are handled by specific rules. If all abstain votes occur, the specification must define exactly what happens. Hidden state produces non-reproducible behavior.

- **Reward hacking opportunities through specification gaps**
  - Example: "agents maximize prosperity"
  - Why: Without a precise formula, "maximize prosperity" can be gamed. Prosperity must be defined as a concrete function of observable variables. Any ambiguity creates exploitation opportunities.

- **Scale mismatch between specification and implementation**
  - Example: "events occur periodically" without defining period
  - Why: Every numerical parameter must be specified. "Periodically" requires a concrete interval (e.g., 1 event per round, or probability distribution over rounds). Implementation must not require inference about scale.

- **Paragraph-only documentation without enumeration**
  - Why: Bullets and enumerated lists ensure complete coverage. Prose paragraphs hide missing cases. If a section uses only paragraphs, it likely has not been fully specified.

- **"TBD" or "to be determined" placeholders in final documents**
  - Why: Any placeholder means the specification is incomplete. Every element must be defined before the specification is considered complete. Placeholders propagate to implementation and create integration failures.

- **Requirements that assume adversarial agent behavior by default**
  - Why: This is a cooperative resource allocation paradigm. The specification should enable cooperative and competitive behavior, but the default assumption is cooperative optimization of collective prosperity. Anti-cooperative mechanics require explicit justification.

- **Missing termination conditions**
  - Why: Every episode must have explicit end conditions. If bankruptcy, max rounds, and prosperity thresholds are not defined, implementations will disagree on episode length. Termination conditions are critical for reproducible evaluation.

- **Unclear visibility boundaries between agents and environment**
  - Why: Every agent's observation must be explicitly defined. If a value is observable, it must be listed in the observation space. If it is hidden, that must be documented. Mixing visibility levels without clear boundaries creates implementation disputes.
