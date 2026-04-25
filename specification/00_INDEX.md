# RL Parliament Environment — Specification Index

> Navigation document for the complete game specification. Use this as your entry point and reference map.

---

## Version Information

| Field | Value |
|-------|-------|
| **Spec Version** | v1.0 |
| **Date** | 2026-04-25 |
| **Status** | Complete |

---

## Document Map

| File | Title | One-Line Summary |
|------|-------|------------------|
| `00_INDEX.md` | Specification Index | This file — navigation and reading guide |
| `01_GAME_OVERVIEW.md` | Game Overview | Concept, inspiration, goals, and environment architecture |
| `02_GAME_RULES_REFERENCE.md` | Game Rules Reference | Single-page complete rules reference for all mechanics |
| `03_TURN_STRUCTURE.md` | Turn Structure | Phase-by-phase turn flow (9 phases per round) |
| `04_ECONOMY_MODEL.md` | Economy Model | Treasury, revenue, treasury surplus, and bankruptcy formulas |
| `05_VOTING_PROTOCOL.md` | Voting Protocol | Voting mechanics, abstention rules, and tie-breaking |
| `06_EVENT_SYSTEM.md` | Event System | Event catalog, severity levels, and hidden impact mechanics |
| `07_AGENT_ACTION_SPACE.md` | Agent Action Space | Valid actions available to ministers each turn |
| `08_OBSERVATION_SPACE.md` | Observation Space | What agents observe about game state |
| `09_REWARD_MODEL.md` | Reward Model | Prosperity calculation and reward formulas |
| `10_SUCCESS_CRITERIA.md` | Success Criteria | Winning/losing conditions, episode boundaries, baselines |
| `11_GUARDRAILS.md` | Guardrails | Explicit exclusions, anti-patterns, and constraints |
| `12_GLOSSARY.md` | Glossary | Defined terms used throughout the specification |
| `13_RL_ADAPTERS_AND_TRAINING.md` | RL Adapters and Training Plan | Implementation-facing policy adapter, telemetry, evaluation, and training contract |
| `APPENDIX_A_EXAMPLES.md` | Example Rounds | Annotated example rounds showing complete gameplay |

---

## Recommended Reading Order

Follow this order for a progressive understanding of the system:

1. **`01_GAME_OVERVIEW.md`** — Start here to understand the core concept, inspiration, and what this environment is trying to achieve
2. **`02_GAME_RULES_REFERENCE.md`** — Get the complete rules in one place before diving into details
3. **`03_TURN_STRUCTURE.md`** — Learn how a round flows through its 9 phases
4. **`04_ECONOMY_MODEL.md`** — Understand treasury management, revenue generation, and surplus mechanics
5. **`05_VOTING_PROTOCOL.md`** — Master how proposals are debated and decided
6. **`06_EVENT_SYSTEM.md`** — Study the events that create dynamic pressure
7. **`07_AGENT_ACTION_SPACE.md`** — See what actions ministers can take
8. **`08_OBSERVATION_SPACE.md`** — Learn what information agents receive
9. **`09_REWARD_MODEL.md`** — Understand how reward is calculated
10. **`10_SUCCESS_CRITERIA.md`** — Learn when the game ends and how performance is measured
11. **`11_GUARDRAILS.md`** — Know the explicit constraints and forbidden actions
12. **`12_GLOSSARY.md`** — Reference defined terms as needed while reading other documents
13. **`13_RL_ADAPTERS_AND_TRAINING.md`** — Read this when implementing adapters, telemetry, evaluation, or training artifacts
14. **`APPENDIX_A_EXAMPLES.md`** — Study concrete examples that tie everything together

---

## How to Use This Spec

### For Hackathon Teams

This specification is the authoritative reference for the RL Parliament Environment. Here is how to approach it based on your role:

**If you are building the environment (engine team):**
- Read documents in order: 01, 02, 03, 04, 05, 06
- Focus on turn structure, economy model, and event system
- Use the glossary (12) when terminology is unclear

**If you are training RL agents (agent team):**
- Read documents in order: 01, 02, 07, 08, 09, 10, 13
- Focus on action space, observation space, and reward model
- Study success criteria (10) to understand your optimization target

**If you are integrating LLM inference (infrastructure team):**
- Read documents in order: 01, 02, 07, 08
- Focus on what agents see (08) and what they can do (07)
- Coordinate with agent team on prompt engineering

**For everyone:**
- Read guardrails (11) early to avoid building forbidden patterns
- Keep glossary (12) handy as a quick reference
- Use appendix examples (APPENDIX_A_EXAMPLES.md) when you need concrete scenarios

### For Multi-Agent RL Researchers

The specification is organized to support iterative deepening:

1. **First pass**: Read 01, 02, 10 to understand the problem space and success metrics
2. **Second pass**: Read 03, 04, 05, 06, 07, 08, 09 to master mechanics
3. **Third pass**: Read 11, 12, APPENDIX_A_EXAMPLES to understand constraints and see examples

### For LLM Reasoning Researchers

Key sections of interest:
- Sequential voting dynamics (05_VOTING_PROTOCOL.md)
- Hidden-information event system (06_EVENT_SYSTEM.md)
- Collective reward structure (09_REWARD_MODEL.md)
- Cooperative vs. competitive baseline comparison (10_SUCCESS_CRITERIA.md)

---

## v1 Departments

The initial department roster for v1:

- Social/Municipal
- Agriculture
- Health
- Education/R&D
- Defense
- Commerce

These six departments form the default parliament. Each minister leads one department and participates in collective budget negotiations.

---

## Document Dependencies

Some documents reference others. Use this map to find related content:

| This Document | Depends On | Referenced By |
|--------------|------------|---------------|
| 03_TURN_STRUCTURE | 02_GAME_RULES_REFERENCE | 07, 08, 09 |
| 04_ECONOMY_MODEL | 02_GAME_RULES_REFERENCE | 09, 10 |
| 05_VOTING_PROTOCOL | 02, 03 | 07 |
| 06_EVENT_SYSTEM | 02, 03, 04 | 08, 10 |
| 07_AGENT_ACTION_SPACE | 02, 03, 05 | 08 |
| 08_OBSERVATION_SPACE | 02, 03, 07 | 09 |
| 09_REWARD_MODEL | 02, 04, 08 | 10 |
| 10_SUCCESS_CRITERIA | 02, 04, 09 | (terminal document) |
| 11_GUARDRAILS | 02, 03 | (referenced by all) |
| 12_GLOSSARY | (references all) | (referenced by all) |
| 13_RL_ADAPTERS_AND_TRAINING | 07, 08, 09, 10, 11 | implementation, evaluation, training |
| APPENDIX_A_EXAMPLES | 02, 03, 04, 05, 06 | (example document) |

---

## Quick Reference

### Key Formulas Location

| Formula | Document |
|---------|----------|
| Treasury calculation | 04_ECONOMY_MODEL |
| Department revenue | 04_ECONOMY_MODEL |
| Efficiency rating | 04_ECONOMY_MODEL |
| Productivity multiplier | 04_ECONOMY_MODEL |
| Voting outcome | 05_VOTING_PROTOCOL |
| Event impact | 06_EVENT_SYSTEM |
| Agent actions | 07_AGENT_ACTION_SPACE |
| Observation values | 08_OBSERVATION_SPACE |
| Prosperity | 09_REWARD_MODEL |
| Reward signal | 09_REWARD_MODEL |
| Episode termination | 10_SUCCESS_CRITERIA |

### Key Constants

| Constant | Value | Document |
|----------|-------|----------|
| Initial treasury | 1000 | 04_ECONOMY_MODEL |
| Baseline tax | 100 per round | 04_ECONOMY_MODEL |
| Initial efficiency | 1.0 | 04_ECONOMY_MODEL |
| Max rounds | 50 | 10_SUCCESS_CRITERIA |
| Prosperity target | 5000 | 10_SUCCESS_CRITERIA |
| Default departments | 6 | This document |

---

*End of Index*