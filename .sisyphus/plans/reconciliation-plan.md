# Reconciliation Plan: Original Design → Current Specs

## TL;DR

> Merge the original piecewise revenue curve design with the current spec's structural framework (Model A consumption, rotating order, no self-voting, population dynamics). This is a **breaking change** to the economic core that affects 10+ documents.
>
> **Deliverables**: Updated economy model, event system, revenue function, population scaling, critical thresholds, and all examples
> **Estimated Effort**: Large (core formulas changing)
> **Parallel Execution**: NO — must be sequential due to dependency chain
> **Critical Path**: Revenue Function Design → Economy Model → Event System → Examples → Cross-Reference Audit

---

## Context

### The Conflict
The current specification uses a **linear efficiency penalty** (`Efficiency = 1.0 - |Allocation - Need|/Need`) that penalizes BOTH over- and under-allocation symmetrically. The original design uses a **piecewise revenue curve** with:
- Critical point (below = game over)
- Demand point (revenue factor = 1.0)
- Surplus point (revenue factor = 1.8, peak profit)
- Wastage point (revenue factor = 1.0)
- Beyond wastage: exponential decay to < 1.0 (loss)

This creates fundamentally different incentives: the original design **rewards moderate over-investment** up to the surplus point, while the current spec **penalizes all deviation from exact need**.

### Original Design Intent (from colleague's analysis + user confirmation)
1. **Piecewise revenue curve**: 4 key points (Critical → Demand → Surplus → Wastage)
2. **Per-sector critical threshold**: Below critical = immediate episode termination
3. **Multiplicative event impacts**: Events scale demand by multiplier (e.g., War → Military demand × 2.5)
4. **Positive events**: Direct treasury cash injection (not need reduction)
5. **Population-scaled demand**: `Need = Baseline × (Pop/Pop₀) + Event`
6. **Persistent productivity**: Running state variable with caps [0.5, 2.0]
7. **Revenue timing**: Same-round application
8. **Population**: 1,000,000 initial
9. **Time mapping**: 3 months per round
10. **Missing events**: Unemployment, teacher shortage, market crash, contamination, public distrust, high public enthusiasm

### What We Keep from Current Specs
- Model A consumption: `Consumption = min(Need, Allocation)`
- Treasury-level surplus: Unspent returns to treasury
- No debt / no deficit spending
- Rotating proposal order (round-robin)
- No self-voting
- Government Shutdown condition (2 rounds zero allocation)
- Collective reward (all agents get identical reward)
- Public debate / public votes
- Event ledger visibility rules
- 9-phase turn structure
- Bankruptcy when Treasury ≤ 0

---

## Work Objectives

### Core Objective
Rewrite the economic engine to match the original piecewise revenue curve design while preserving all structural and procedural mechanics from the current specs.

### Concrete Deliverables
- Updated `04_ECONOMY_MODEL.md` with piecewise revenue function
- Updated `06_EVENT_SYSTEM.md` with multiplicative events and treasury injections
- Updated `09_REWARD_MODEL.md` with persistent productivity
- Updated `10_SUCCESS_CRITERIA.md` with critical thresholds
- Updated `02_GAME_RULES_REFERENCE.md` with new revenue rules
- Updated `03_TURN_STRUCTURE.md` with same-round revenue and time mapping
- Updated `APPENDIX_A_EXAMPLES.md` with recalculated examples
- Updated `12_GLOSSARY.md` with new terms
- Updated `01_GAME_OVERVIEW.md` with time mapping

### Definition of Done
- [ ] Revenue function implements 4-point piecewise curve exactly as drawn
- [ ] Per-sector critical threshold causes immediate game-over
- [ ] Events use multiplicative demand scaling
- [ ] Positive events inject cash into treasury
- [ ] Demand scales with population
- [ ] Productivity is persistent with caps [0.5, 2.0]
- [ ] Revenue applies same-round
- [ ] Population = 1,000,000
- [ ] All examples recalculated with new formulas
- [ ] Cross-reference audit passes

### Must Have
- Piecewise revenue curve matching the hand-drawn diagram
- Critical threshold game-over condition
- Multiplicative event impacts
- Treasury-injecting positive events
- Population-scaled demand
- Persistent productivity with caps
- Same-round revenue application

### Must NOT Have
- Linear efficiency penalty (current spec)
- Additive event costs (current spec)
- Need-reducing positive events (current spec)
- Recalculated-each-round productivity (current spec)
- Next-round revenue delay (current spec)
- Population = 1 or inconsistent values

---

## Verification Strategy

### QA Policy
Every task MUST include agent-executed QA. Evidence saved to `.sisyphus/evidence/recon-{N}-{scenario}.{ext}`.

- **Documentation**: Read files, verify formulas match design, check examples
- **Mathematical verification**: Verify revenue curve at key points (A, B, C, D)
- **Cross-reference**: Check consistency between economy, event, and reward docs

---

## Execution Strategy

### Sequential Execution (Due to Dependency Chain)

```
Wave 1 — Foundation (must complete before Wave 2):
├── Task 1: Design piecewise revenue function (mathematical specification)
└── Task 2: Design persistent productivity system

Wave 2 — Core Documents (depends on Wave 1):
├── Task 3: Rewrite 04_ECONOMY_MODEL.md
├── Task 4: Rewrite 06_EVENT_SYSTEM.md
└── Task 5: Update 03_TURN_STRUCTURE.md (same-round revenue, time mapping)

Wave 3 — Dependent Documents (depends on Wave 2):
├── Task 6: Rewrite 09_REWARD_MODEL.md
├── Task 7: Update 02_GAME_RULES_REFERENCE.md
├── Task 8: Update 10_SUCCESS_CRITERIA.md
├── Task 9: Update 01_GAME_OVERVIEW.md
└── Task 10: Update 12_GLOSSARY.md

Wave 4 — Integration (depends on Wave 3):
├── Task 11: Rewrite APPENDIX_A_EXAMPLES.md
└── Task 12: Cross-reference consistency audit

Wave FINAL:
├── Task F1: Oracle compliance audit
├── Task F2: Mathematical verification of revenue curve
└── Task F3: Final user approval
```

---

## TODOs

---

## Final Verification Wave

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Verify: all 4 revenue curve points implemented, critical threshold exists, multiplicative events, treasury injections, population scaling, persistent productivity, same-round revenue, all examples correct.

- [ ] F2. **Mathematical Verification** — `unspecified-high`
  Verify revenue function at: x = Critical (y=0), x = Demand (y=1.0), x = Surplus (y=1.8), x = Wastage (y=1.0), x > Wastage (y < 1.0), x < Critical (game over).

- [ ] F3. **User Approval** — `deep`
  Present final spec to user. Get explicit "okay" before marking complete.

---

## Commit Strategy

- **Wave 1**: `docs(spec): add piecewise revenue function and persistent productivity design`
- **Wave 2**: `docs(spec): rewrite economy model and event system for piecewise revenue`
- **Wave 3**: `docs(spec): update reward, rules, success criteria, glossary`
- **Wave 4**: `docs(spec): rewrite examples and cross-reference audit`
- **FINAL**: `docs(spec): complete reconciliation with original design`

---

## Success Criteria

- [ ] Revenue curve matches hand-drawn diagram at all 4 points
- [ ] Critical threshold causes game-over when Allocation < Critical
- [ ] Events use multiplicative demand scaling
- [ ] Positive events inject cash into treasury
- [ ] Demand formula includes population scaling
- [ ] Productivity is persistent with caps [0.5, 2.0]
- [ ] Revenue applies same-round
- [ ] All 14 documents are consistent
- [ ] All examples use correct formulas
- [ ] No "TBD" or ambiguous placeholders
