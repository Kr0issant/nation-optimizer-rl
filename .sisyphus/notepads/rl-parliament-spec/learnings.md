# RL Parliament Spec - Learnings

## Task 2: Game Rules Reference

### Completed
- Created `specification/02_GAME_RULES_REFERENCE.md` as single-page anchor document
- Document uses MUST/MAY NOT/MAY language throughout (41 occurrences)
- All 8 required section headings present: Agents/Ministers, Treasury & Budget, Budget Proposals, Voting, Events, Surplus & Rollover, Bankruptcy, Revenue & Productivity
- One concrete example included (6-minister Health ministry with 300-unit proposal)
- Zero TBD/TODO/FIXME found
- No paragraphs without bullet points

### Verification Results
- `grep -c "MUST\|MAY NOT"` = 41 (exceeds ≥10 requirement)
- `grep -c "TBD\|TODO\|FIXME"` = 0 (passes)
- All subheadings present and properly marked with ##

## Task 1 Complete: 01_GAME_OVERVIEW.md

**Completed**: 2025-04-25

**Verification Results**:
- File created at `specification/01_GAME_OVERVIEW.md` (85 lines)
- 42 bullet points under subheadings (not paragraph-only)
- Required sections present: Concept, Inspiration, Goals, Non-Goals, Target Audience, Core Mechanics Summary, Environment Architecture, Reward Model, Key Constraints
- Marxist doctrine referenced explicitly: "From each according to his ability, to each according to his need"
- Variable even agent count mentioned: 4, 6, 8+ ministers
- No "TBD" or ambiguous placeholders found

**Key Design Decisions Recorded**:
- Collective reward is global, not per-agent
- No debt constraint explicitly documented
- Stochastic events with hidden costs mentioned
- Sequential voting with abstention allowed noted
- Departmental surplus rollover noted as mechanic

**Evidence**: `.sisyphus/evidence/task-1-structure-check.txt`

## Task 3: Turn Structure

### Completed
- Created `specification/03_TURN_STRUCTURE.md` defining 9-phase turn flow
- Explicitly states events revealed BEFORE proposals (Phase 1 vs Phase 3)
- Explicitly states revenue calculated AFTER consumption (Phase 7, applies next round)
- Includes treasury timing table showing debit/credit timing per phase
- Zero TBD/TODO/FIXME found
- No paragraphs without bullet points

### Verification Results
- All 9 phases have clear ordering (numbered 1-9)
- Event revelation timing: Phase 1 (BEFORE proposals)
- Revenue timing: Phase 7 (AFTER consumption in Phase 6)
- Treasury debit: Phase 5 only (after voting)
- Treasury credit: Never same-round (revenue applies next round)
- Critical design notes section explains uncertainty-driven learning rationale

## Task 4: Glossary Seed

**Completed**: 2025-04-25

**Verification Results**:
- File created at `specification/12_GLOSSARY.md` (18 terms)
- 18 defined terms (exceeds ≥15 requirement)
- Zero TBD found
- Alphabetical order verified
- All 18 required terms present

**Terms Defined** (alphabetical):
Agent/Minister, Bankruptcy, Baseline Tax Revenue, Budget, Central Treasury, Department, Episode, Event, Event Ledger, Portfolio, Productivity, Proposal, Prosperity, Revenue, Severity, Surplus, Term/Round, Vote

## Task 5: Guardrails

**Completed**: 2025-04-25

**Verification Results**:
- File created at `specification/11_GUARDRAILS.md` (107 lines)
- 16 explicit guardrails with "NO" prefix (exceeds ≥10 requirement)
- 27 "Why:" explanations (one per guardrail plus AI slop patterns)
- "AI Slop Patterns to Avoid" section present with 10 anti-patterns
- 4 required sections: Scope Guardrails, Mechanic Guardrails, Implementation Guardrails, AI Slop Patterns to Avoid
- Zero "TBD" found (only mention is in AI slop anti-pattern section as forbidden pattern)
- Bullet-point format throughout

**Guardrails Count by Section**:
- Scope Guardrails: 5 guardrails
- Mechanic Guardrails: 7 guardrails
- Implementation Guardrails: 5 guardrails
- AI Slop Patterns to Avoid: 10 anti-patterns

**Evidence**: `.sisyphus/evidence/task-5-guardrails-check.txt`

## Task 6: Voting Protocol

**Completed**: 2025-04-25

**Verification Results**:
- File created at `specification/05_VOTING_PROTOCOL.md`
- All 5 required checklist items present:
  - Majority threshold defined (>50% of non-abstaining)
  - Tie-breaking rule defined (tie = rejection)
  - Abstention rules for proposing and voting defined
  - Approval/rejection consequences defined
  - Edge cases covered (all abstain, tie, exceeds treasury, late proposal)
- 9 edge cases enumerated covering all required scenarios
- Summary table included with 7 scenarios
- Zero "TBD" found
- Bullet-point format throughout
- Debates rules aligned with Phase 2 in 03_TURN_STRUCTURE.md

**Edge Cases Covered**:
- All abstain from voting → REJECTED
- Tie vote → REJECTED
- Proposal exceeds treasury → REJECTED auto before voting
- Late submission → INVALID ignored
- Treasury negative after approval → Bankruptcy triggered
- Sequential treasury depletion → later proposals auto-rejected
- All abstain from proposing → game proceeds
- Single minister remaining scenarios
- Minister votes on own proposal → ALLOWED

**Key Design Decisions Recorded**:
- Strict majority required (50% + 1)
- Tie = rejection (no chair vote or random break)
- Abstentions not counted toward majority
- Debate occurs Phase 2 BEFORE proposals in Phase 3

## Task 7: Economy Model

**Completed**: 2025-04-25

**Verification Results**:
- File created at `specification/04_ECONOMY_MODEL.md`
- All 8 required checklist items present:
  - Treasury calculation formula: `Treasury_t = Baseline_Tax + Productivity_Bonus_{t-1} + Sum(Department_Revenues_{t-1})`
  - Baseline Tax Revenue: 100 units per round (constant)
  - Productivity formula: `Productivity_Bonus_d = Surplus_d * Efficiency_Rating_d * 0.5`
  - Department Revenue formula: `Department_Revenue_d = Allocation_d * Efficiency_Rating_d * Productivity_Multiplier`
  - Efficiency Rating formula: `Efficiency_Rating_d = 1.0 + (Surplus_d / Allocation_d)`
  - Surplus rollover: `Surplus_{d,t+1} = Surplus_{d,t} + (Allocation_{d,t} - Consumption_{d,t})`
  - Bankruptcy: `Treasury_t <= 0 OR Department_Deficit_d > 0`
  - Starting treasury: 1000 units
- 3 numerical examples included showing formulas in action
- Summary table with 8 key formulas present
- Zero "TBD" found
- Bullet-point format throughout
- Design rationale section explaining feedback loop mechanics

**Formulas Documented**:
| Formula | Purpose |
|----------|---------|
| `Treasury_t` | Central treasury calculation at round start |
| `Baseline_Tax` | Constant 100 units per round |
| `Department_Revenue_d` | Per-department revenue generation |
| `Efficiency_Rating_d` | Efficiency based on surplus proportion |
| `Productivity_Multiplier` | Global multiplier based on total surplus |
| `Productivity_Bonus_d` | Bonus for sustained efficiency |
| `Surplus_d` | Department surplus calculation |
| `Surplus_{d,t+1}` | Surplus rollover to next round |

**Key Design Decisions Recorded**:
- Revenue from round T applies to round T+1 treasury (delayed feedback)
- Efficiency Rating minimum is 1.0 (no negative efficiency floor)
- Surplus capped at 2x allocation to prevent unbounded accumulation
- Deficit reduces efficiency by 0.1 per unit (penalty for overspending)
- Global Productivity Multiplier rewards system-wide efficiency

## Task 8: Event System

**Completed**: 2025-04-25

**Verification Results**:
- File created at `specification/06_EVENT_SYSTEM.md`
- All 8 required checklist items present:
  - Event generation rules: 80% chance 1 event, 20% chance 2 events, 0% chance 0 events
  - Maximum 2 events per round (enforced by Guardrails)
  - Severity levels 1-5 with names and meanings
  - 8 example events cataloged (exceeds ≥5 requirement)
  - Positive events included (Medical Breakthrough, Economic Boom)
  - Event cost formula: `Event_Cost = Base_Cost * Severity_Multiplier * Random_Variance`
  - What agents observe vs what is hidden clearly documented
  - Department relevancy mapping table included
- 8 events cataloged: War, Famine, Virus Outbreak, Medical Breakthrough, Infrastructure Collapse, Economic Boom, Education Reform, Budget Crisis
- Zero "TBD" found
- Bullet-point format throughout
- Event Ledger section defined (append-only per episode)

**Event Catalog Coverage**:
| Event | Department | Severity | Type |
|-------|-----------|----------|------|
| War | Defense | 3-5 | Negative |
| Famine | Agriculture | 2-4 | Negative |
| Virus Outbreak | Health | 2-5 | Negative |
| Medical Breakthrough | Health | 1-2 | Positive |
| Infrastructure Collapse | Infrastructure | 3-4 | Negative |
| Economic Boom | All | 1-2 | Positive |
| Education Reform | Education | 2-3 | Negative |
| Budget Crisis | Economy | 2-3 | Negative |

**Key Design Decisions Recorded**:
- Events revealed BEFORE proposals (Phase 1 of Turn Structure)
- Agents see narrative + severity but NOT exact cost
- Exact cost revealed only after round resolves
- Positive events reduce costs (negative Base_Cost = credit)
- Negative events increase costs (positive Base_Cost = debit)
- Random_Variance uniform [0.8, 1.2] provides unpredictability

## Task 9: Agent Action Space

**Completed**: 2025-04-25

**Verification Results**:
- File created at `specification/07_AGENT_ACTION_SPACE.md` (272 lines)
- All 4 required actions enumerated:
  1. PROPOSE_BUDGET — submit budget for own department (Phase 3)
  2. VOTE — cast vote on proposal (Phase 4)
  3. DEBATE — send public message (Phase 2)
  4. ABSTAIN_FROM_PROPOSAL — skip turn (Phase 3)
- All constraints defined for each action
- Phase-action mapping table included
- Invalid action handling documented (5 scenarios)
- State transition diagram included
- Zero "TBD" found
- Bullet-point format throughout

**Actions Enumerated**:
| Action | Parameters | Phase | Constraint |
|--------|------------|-------|------------|
| PROPOSE_BUDGET | department, amount, justification | Phase 3 | 0 <= amount <= treasury |
| VOTE | proposal_id, vote | Phase 4 | proposal must exist |
| DEBATE | message | Phase 2 | none |
| ABSTAIN_FROM_PROPOSAL | none | Phase 3 | must be agent's turn |

**Invalid Action Handling Coverage**:
- Invalid amount (negative, exceeds treasury, non-numeric) → REJECTED
- Wrong department → REJECTED
- Action outside correct phase → IGNORED
- Multiple proposals by same agent → first accepted, rest ignored
- Vote on non-existent proposal → IGNORED

**Edge Cases Documented**:
- Agent submits invalid proposal multiple times
- Agent attempts action during system phase (Phase 5-9)
- Sequential proposal depletion affects later proposals

**Key Design Decisions Recorded**:
- Actions are phase-restricted (cannot vote during proposal phase)
- Proposals must be within valid range (0 to treasury balance)
- Debate is public only (no private communication)
- Abstention is explicit action, not passive
- Agents can abstain from proposing but must explicitly vote (or abstain from voting)
- Invalid actions never partially modify state
- Re-submission allowed until phase ends or valid submission accepted

## Task 10: Observation Space

**Completed**: 2025-04-25

**Verification Results**:
- File created at `specification/08_OBSERVATION_SPACE.md` (349 lines)
- All 6 required checklist items present:
  - Observation defined for each of 9 phases
  - Public vs private vs hidden information clearly distinguished
  - Concrete example observation included (Health agent in Phase 3)
  - Both structured data (JSON) and natural language formats defined
  - Visibility matrix table included
  - Zero "TBD" found
  - Bullet-point format throughout

**Phase-by-Phase Observation Coverage**:
| Phase | Key Observations |
|-------|-----------------|
| 1 (Event Revelation) | Event ledger update, severity, narrative, affected departments |
| 2 (Debate) | Treasury, debate messages, own department status |
| 3 (Proposal) | All proposals so far, treasury, own previous allocation |
| 4 (Voting) | All proposals, all votes cast, treasury |
| 5 (Budget Execution) | Approved proposals, treasury after debit |
| 6 (Consumption/Event Impact) | Event costs revealed, treasury unchanged |
| 7 (Revenue Calculation) | Treasury unchanged, revenue internal |
| 8 (Surplus Rollover) | Own surplus/deficit update |
| 9 (Termination Check) | Termination status, final treasury, prosperity score |

**Information Visibility Matrix**:
| Information | All See | Own Only | Hidden |
|-------------|---------|----------|--------|
| Treasury | Yes | | |
| Events (name/narrative/severity) | Yes | | |
| Event exact cost | | | Yes (until round ends) |
| All debate messages | Yes | | |
| All proposals | Yes | | |
| All votes | Yes | | |
| Own allocation/surplus | | Yes | |
| Other department private state | | | Yes |
| Round number | Yes | | |

**Key Design Decisions Recorded**:
- Treasury fully public at all times
- All votes public (no secret ballots)
- All debate public (no private communication per Guardrails)
- Event exact cost hidden until after round resolves (per Event System)
- Department-level consumption, surplus, efficiency rating are PRIVATE to that department
- Only own_department field exposes private data to each agent
- Agents see event cost NULL until Phase 6, then filled in
- Revenue calculations are internal and not disclosed to agents directly

**Format Definitions**:
- Structured Data: JSON-like format with round, phase, treasury, event_ledger, proposals, votes, debate_messages, own_department, termination fields
- Natural Language: Human-readable summary for LLM agent prompts
- Both formats provided side-by-side in spec

## Task 11: Reward Model

**Completed**: 2025-04-25

**Verification Results**:
- File created at `specification/09_REWARD_MODEL.md` (272 lines)
- All 8 required checklist items present:
  - Exact reward formula documented: `R_t = Base_Reward_t + Productivity_Bonus_t + Efficiency_Bonus_t + Survival_Bonus_t + Allocation_Penalty_t - Bankruptcy_Penalty_t`
  - Prosperity defined mathematically: `Prosperity_t = (Total_Revenue_t + Treasury_Balance_t) / Population`
  - Per-step vs per-episode rewards specified (per-step at Phase 9, episode = sum)
  - Collective reward only (all agents identical, no individual component)
  - 3 numerical examples included (Normal Growth, Crisis Management, Bankruptcy)
  - Bullet-point format throughout
  - Zero "TBD" found

**Reward Components Documented**:
| Component | Formula | Range |
|-----------|---------|-------|
| Base Reward | `Prosperity_t` | (-inf, +inf) |
| Productivity Bonus | `+10 * Sum(Surplus_d_t where Surplus > 0)` | [0, +inf) |
| Efficiency Bonus | `+5 * Count(Efficiency_Rating_d_t > 1.0)` | [0, +inf) |
| Survival Bonus | `+1 * Rounds_Survived_t` | [0, +inf) |
| Over-Allocation Penalty | `-5 * Count(over-allocated without gains)` | (-inf, 0] |
| Under-Allocation Penalty | `-10 * Count(over-consumed)` | (-inf, 0] |
| Bankruptcy Penalty | `-1000 if bankrupt else 0` | {-1000, 0} |

**Alternative Prosperity Formulas Provided**:
- Option A (Recommended): Revenue-Based — `(Total_Revenue_t + Treasury_Balance_t) / Population`
- Option B: Efficiency-Weighted — `Sum(Department_Revenue_d_t * Efficiency_Rating_d_t) / Population`
- Option C: Surplus-Driven — `(Baseline_Tax + Sum(Surplus_d_t)) / Population`

**Key Design Decisions Recorded**:
- Collective reward aligns with parliamentary cooperation requirement
- Prosperity as GDP per capita provides intuitive, economically grounded signal
- Productivity bonus incentivizes under-spending relative to allocation (positive-sum behavior)
- Efficiency bonus rewards departments operating above baseline (encourages optimization)
- Survival bonus discourages reckless behavior that triggers bankruptcy
- Under-allocation penalty discourages under-funding critical departments
- Bankruptcy penalty creates strong incentive to avoid treasury depletion or deficit spending
- No individual component prevents zero-sum competition between ministers
- Reward timing: calculated at Phase 9 (Termination Check) of each round

**Numerical Examples Covered**:
1. Normal Growth Round: 4 departments, reward = 1405
2. Crisis Management Round: 4 departments tight budgets, reward = 640
3. Bankruptcy Scenario: treasury reaches 0, reward = -732 (episode terminated)

## Task 10: Success Criteria

**Completed**: 2025-04-25

**Verification Results**:
- File created at `specification/10_SUCCESS_CRITERIA.md` (209 lines)
- All 5 required checklist items present:
  - Episode termination conditions: Bankruptcy (treasury <= 0 OR department deficit > 0), Max rounds (50), Prosperity threshold (5000 for 3 consecutive rounds)
  - Success metrics: Survival time, Final prosperity, Budget balance ratio, Efficiency score, Revenue generation rate, Treasury stability
  - Episode boundaries: Start (round 0, treasury 1000, all surplus 0, efficiency 1.0) and End (any termination condition met)
  - Baseline comparisons: Random agent (10-15 rounds, prosperity 200-400), Greedy agent (5-10 rounds, prosperity 100-200), Cooperative baseline (20-30 rounds, prosperity 800-1500)
  - Scoring rubric for hackathon judging: Exceptional, Strong, Competent, Developing, Failed tiers
- Zero "TBD" found
- Bullet-point format throughout
- Metric collection protocol defined for per-round and episode-end metrics

**Success Tiers Documented**:
| Tier | Criteria |
|------|----------|
| Exceptional | Reaches prosperity 5000+ by round 30 OR survives 50 rounds with final prosperity > 3000 |
| Strong | Survives 40+ rounds with final prosperity > 2000 |
| Competent | Survives 25+ rounds with final prosperity > 1000 |
| Developing | Survives 15+ rounds with final prosperity > 500 |
| Failed | Bankruptcy before round 15 |

**Baseline Comparisons Documented**:
| Baseline | Expected Survival | Expected Final Prosperity |
|----------|------------------|---------------------------|
| Random Agent | 10-15 rounds | 200-400 |
| Greedy Agent | 5-10 rounds | 100-200 |
| Cooperative | 20-30 rounds | 800-1500 |

**Key Design Decisions Recorded**:
- Survival time is primary metric (incentivizes avoiding risky behavior)
- Prosperity threshold requires 3 consecutive rounds (prevents luck-based wins)
- Three baseline levels enable clear progress measurement
- Hackathon rubric enables quick judge evaluation
- Bankruptcy is immediate termination with -1000 penalty
- State transitions explicitly documented (Start -> Phase 1-9 -> Termination Check -> Continue/Terminate)

## Task 12: Appendix A Examples

**Completed**: 2025-04-25

**Verification Results**:
- File created at `specification/APPENDIX_A_EXAMPLES.md` (507 lines)
- All 4 required examples present:
  1. Normal Round: 6 departments, treasury 1000 -> 180, 80 total surplus generated, round 2 treasury 1136.3
  2. Crisis Round: War + Virus outbreak, Health proposal rejected (tie 3-3), near-bankruptcy with deficits
  3. All Abstain Edge Case: No proposals, baseline consumption drains treasury from 393.6 to 93.6
  4. Surplus Rollover: Efficiency bonus demonstration across 2 rounds with surplus carryover
- v1 department roster used: Social/Municipal, Agriculture, Health, Education/R&D, Defense, Commerce
- All 9 phases shown in each example
- All formulas from Economy Model applied with concrete numbers
- Voting results show majority calculations (YES > NO of non-abstaining)
- Tie = rejection rule demonstrated in Crisis Round example
- Zero "TBD" found
- Bullet-point format with round subheadings
- Summary table of formulas included at end

**Examples Detail**:
| Example | Type | Key Outcome |
|---------|------|-------------|
| Normal Round | Standard | Treasury 1000 -> 1136.3 (+13.6%) via efficiency gains |
| Crisis Round | Standard | Health rejected (tie), multiple deficits, treasury 479.9 |
| All Abstain | Edge Case | Treasury drained 393.6 -> 93.6 via baseline consumption |
| Surplus Rollover | Edge Case | Efficiency bonus compounds across rounds |

**Formulas Applied in Examples**:
- Treasury_t = Baseline_Tax + Productivity_Bonus + Sum(Department_Revenues)
- Efficiency_Rating_d = 1.0 + (Surplus_d / Allocation_d)
- Productivity_Multiplier = 1.0 + (Total_Surplus / Total_Allocation)
- Department_Revenue_d = Allocation × Efficiency × Productivity_Multiplier
- Event_Cost = Base_Cost × Severity_Multiplier × Random_Variance

**Key Design Decisions Recorded**:
- Concrete numbers in all cells (no vague amounts)
- Crisis example shows tie rejection and sequential treasury depletion
- Surplus rollover example demonstrates self-reinforcing efficiency mechanic
- Edge case (all abstain) shows treasury drains even without explicit allocations

---

## F1: Plan Compliance Audit (2026-04-25)

**Audit Result**: ✅ **COMPLIANT**

### Verification Summary

| Check | Result |
|-------|--------|
| File count = 14 | ✅ PASS (14 files found) |
| No "TBD" or placeholders | ✅ PASS (only in AI slop anti-pattern docs as example) |
| Bullet-point format | ✅ PASS (all docs use enumerated lists) |
| Must Have items | ✅ PASS (all requirements met) |
| Must NOT Have items | ✅ PASS (no implementation code found) |
| Cross-references resolve | ✅ PASS (all referenced docs exist) |

### Must Have Items Verification

All 14 documents contain required items:

| Doc | Requirement | Status |
|-----|-------------|--------|
| 01 | Concept, Inspiration, Goals, Non-Goals | ✅ |
| 02 | Agents, Treasury, Proposals, Voting, Events, Surplus, Bankruptcy, Revenue | ✅ |
| 03 | 9 numbered phases | ✅ |
| 04 | Treasury formula, baseline, productivity, surplus, bankruptcy | ✅ |
| 05 | Majority, tie-breaking, abstention, approval/rejection, edge cases | ✅ |
| 06 | Event frequency, ≥5 examples, severity, hidden costs, relevancy | ✅ (7 events) |
| 07 | All actions enumerated, constraints, invalid handling, phase mapping | ✅ |
| 08 | Observations per phase, public/private, example, format | ✅ |
| 09 | Reward formula, prosperity definition, per-step, collective, examples | ✅ |
| 10 | Termination conditions, metrics, baselines, boundaries | ✅ |
| 11 | ≥10 guardrails, Why explanations, AI Slop section | ✅ (16 guardrails) |
| 12 | ≥15 terms, alphabetical, 1-2 sentence definitions | ✅ (16 terms) |
| 00 | 14 docs listed, reading order, How to Use, version | ✅ |
| APPENDIX | ≥2 examples, ≥1 edge case, concrete numbers | ✅ (4 examples) |

### Must NOT Have Items Verification

| Item | Check | Result |
|------|-------|--------|
| Implementation code | No `def `, `function `, `class ` in spec docs | ✅ |
| "TBD" placeholders | Only in AI slop anti-pattern section as example | ✅ |
| Paragraph-only docs | All docs use bullet points | ✅ |
| Ambiguous terms | Cross-checked glossary vs body | ✅ |
| Training algorithm scope creep | No PPO/A3C/REINFORCE mentions | ✅ |

### Cross-References Verified

All cross-references resolve to existing files. 12_GLOSSARY.md contains the most cross-references and all point to existing documents.

### Exception: JSON Code Blocks

08_OBSERVATION_SPACE.md contains JSON code blocks (lines 173, 286) showing observation format. These are acceptable as they document data structure formats, not implementation code.

### Evidence Location

Full audit report saved to: `.sisyphus/evidence/f1-compliance-report.md`
