# Proposed Amendment — Fixing Critical Threshold, Abstention, and Voting Contradictions

> Status: **Under deliberation**  
> Scope: Economy model, voting protocol, termination conditions, action space  
> Impact: HIGH — changes core game loop mechanics

---

## 1. Problem Statement

The current specification and codebase contain **three mutually incompatible rules** that create broken game logic:

### Contradiction A: Abstention vs. Critical Failure
- **Spec (02_GAME_RULES_REFERENCE:14)**: "A minister MAY abstain from proposing a budget for their own department in any round"
- **Spec (04_ECONOMY_MODEL:175)**: "If `Allocation_d < Critical_d` for **ANY** department, the episode terminates immediately with **CRITICAL FAILURE**"
- **Math**: Abstention → Allocation = 0 → 0 < Critical (≈40% of demand) → **GAME OVER**
- **Result**: The "MAY abstain" permission is actually a **suicide button**. It cannot be used safely.

### Contradiction B: Rejection vs. Critical Failure
- **Spec (05_VOTING_PROTOCOL)**: Proposals can be rejected by majority NO vote or tie
- **Math**: Rejection → Allocation = 0 → 0 < Critical → **GAME OVER**
- **Result**: Any rational agent will **never vote NO**, because rejecting any proposal ends the episode. Voting becomes ceremonial.

### Contradiction C: Safe Abstention vs. Spec Intent
- **Current code (core/game.py:488-498)**: Critical check is restricted to `approved_departments` only. Abstainers/rejected departments are skipped.
- **Result**: Abstention is a **dominant strategy** — it lets a department skip its turn with zero risk. This contradicts the spec's intent that underfunding is lethal.

### Contradiction D: Unwinnable Treasury States
- **Math**: Total critical for 6 departments ≈ 190. Baseline tax = 100.
- If treasury drops below 190 (through poor revenue, crises, or waste), **any** allocation that satisfies critical bankrupts the treasury, and **any** affordable allocation triggers critical failure.
- **Result**: The game can enter a mathematically unwinnable state through no fault of a single bad decision, but through accumulated drift.

---

## 2. Root Cause Analysis

The core issue is that **survival funding** and **discretionary investment** are conflated into a single budget proposal. When a minister proposes, they are asking for both:
1. The minimum needed to keep the department alive (`Critical`)
2. The amount needed for the department to generate revenue and contribute to the economy (`Demand` and above)

Because these are bundled, rejecting a proposal or abstaining strips away **both** — killing the department and ending the episode. There is no way for parliament to say "we'll fund your survival but not your growth."

The fix requires **separating survival baseline from discretionary ask**.

---

## 3. Proposed Solution Options

### Option A: Auto-Fund Critical + Discretionary Proposals (RECOMMENDED)

**Mechanic:**
- **Phase 5 (Budget Execution) — Step 0: Auto-Fund Critical**
  - Before any voted proposals are executed, each department automatically receives `Critical_d = Demand_d × 0.4`
  - This amount is deducted from treasury unconditionally
  - If treasury < `sum(Critical_d)`, episode ends with **BANKRUPTCY** (not critical failure)
  - Revenue factor at `Allocation = Critical` is 0.0, so auto-funded critical generates **zero revenue** — it is pure survival cost

- **Phase 3 (Budget Proposal): Discretionary Proposals Only**
  - Ministers propose amounts **above their critical baseline** (i.e., additional funding they want)
  - Proposal amount must be ≥ 0
  - A proposal of 0 means "I only need the automatic critical, no extra"
  - **ABSTENTION IS REMOVED** — every minister must submit a proposal (even if 0)

- **Phase 5 (Budget Execution) — Step 1: Execute Approved Discretionary**
  - Approved discretionary amounts are added to the auto-funded critical
  - Total allocation = `Critical_d + Discretionary_d`
  - Revenue factor is computed on the **total allocation**
  - Treasury is debited for approved discretionary amounts
  - Sequential depletion still applies: if early approvals deplete treasury, later discretionary proposals are auto-rejected

- **Critical Check**: Simplified or removed
  - Since every department is guaranteed at least `Critical_d`, critical failure is **impossible by design**
  - Remove `CRITICAL_FAILURE` as a separate termination reason
  - Keep only: BANKRUPTCY, SHUTDOWN, MAX_ROUNDS, PROSPERITY_THRESHOLD

- **Shutdown Condition**: Redefine
  - Current: `sum(Allocation_d) = 0` for 2 rounds
  - New: `sum(Discretionary_d) = 0` for 2 rounds (or remove entirely)
  - Since auto-critical is always > 0, the old shutdown condition would never trigger

**Example with 6 departments (no events, pop=1M):**

| Department | Critical | Demand | Discretionary Ask | Approved? | Total Alloc | RF | Revenue |
|---|---|---|---|---|---|---|---|
| Social | 24 | 60 | 20 | YES | 44 | 0.556 | 24.4 |
| Agriculture | 28 | 70 | 30 | YES | 58 | 0.714 | 41.4 |
| Health | 36 | 90 | 0 | — | 36 | 0.0 | 0.0 |
| Education | 32 | 80 | 40 | YES | 72 | 0.875 | 63.0 |
| Defense | 40 | 100 | 50 | NO | 40 | 0.0 | 0.0 |
| Commerce | 30 | 75 | 25 | YES | 55 | 0.714 | 39.3 |
| **Totals** | **190** | **—** | **—** | **—** | **305** | **—** | **168.1** |

Treasury update: `1000 + 100 + 168.1 - 305 = 963.1` (declining because not enough discretionary)

**Pros:**
- Voting is **meaningful**: YES = fund growth, NO = survival only
- No sudden death from rejection or abstention
- Truthfulness is incentivized: ministers can honestly state what they need without fear of death
- Treasury tension is preserved: auto-critical is a fixed cost, profit only comes from discretionary
- Mathematically impossible to have a "critical failure" that isn't already "bankruptcy"

**Cons:**
- Changes the economy model (split into mandatory + discretionary)
- Auto-critical is pure cost (RF=0), making the treasury bleed by default
- Agents may struggle to learn that they MUST spend discretionary to survive
- Requires removing CRITICAL_FAILURE as a termination condition

**Spec files to change:** `02_GAME_RULES_REFERENCE`, `03_TURN_STRUCTURE`, `04_ECONOMY_MODEL`, `05_VOTING_PROTOCOL`, `07_AGENT_ACTION_SPACE`, `10_SUCCESS_CRITERIA`

**Code files to change:** `core/game.py` (auto-fund logic, remove abstention), `core/reward.py` (remove critical penalty), `schemas/actions.py` (remove ABSTAIN_FROM_PROPOSAL), `schemas/phases.py`, agent adapters

---

### Option B: Safe Abstention + Restricted Critical Check (Match Current Code)

**Mechanic:**
- Keep the current code behavior exactly as-is
- Critical check applies **only to departments with approved proposals**
- Abstaining departments and rejected proposals receive 0 allocation but are **not checked**
- Update the specification to match the code: "Critical failure applies only to departments that received an approved allocation"
- Keep ABSTAIN_FROM_PROPOSAL as a valid action

**Pros:**
- Minimal code change (mostly spec updates)
- Voting remains meaningful: rejecting a proposal is safe for the target department
- Ministers can strategically abstain to avoid risky proposals

**Cons:**
- Abstention is a **dominant strategy**: it lets you skip your turn with zero risk
- RL agents will learn to **never propose** — they can just abstain and free-ride on others
- Breaks the spec's original intent that underfunding is lethal
- Creates a "tragedy of the commons" where everyone abstains and nothing gets funded

**Verdict:** Not recommended for training. Agents will exploit this immediately.

---

### Option C: Default Critical on Rejection/Abstention

**Mechanic:**
- If a proposal is **rejected**, the department still receives `Critical_d` automatically
- If a minister **abstains**, the department still receives `Critical_d` automatically
- Treasury deducts `Critical_d` for every department, every round, unconditionally
- Critical check still runs but always passes because everyone gets at least critical
- Ministers propose **total** amounts (not discretionary), but rejection auto-bumps to critical

**Example:**
- Defense proposes 150 (demand=100, critical=40)
- Proposal rejected → Defense gets 40 anyway
- Revenue computed on 40 (RF=0) → no revenue from Defense this round

**Pros:**
- Rejection doesn't kill anyone
- Voting is meaningful: you're deciding between "full ask" vs. "bare minimum"
- No change to how ministers frame proposals (still total amounts)

**Cons:**
- Counter-intuitive: "rejected" proposal still costs treasury
- Creates perverse incentives: propose extremely high amounts knowing you'll get critical even if rejected
- Hard to explain in the spec why a "rejected" proposal still gets funded
- The auto-bump logic is hidden and confusing

**Verdict:** Less clean than Option A. The "rejected but funded" mechanic is a smell.

---

### Option D: Remove Critical Failure, Replace with Gradual Penalty

**Mechanic:**
- Remove the hard `CRITICAL_FAILURE` game-over condition entirely
- Below critical: department generates **zero revenue** and applies a `-0.01` productivity penalty
- Between critical and demand: normal linear RF as currently specified
- Sustained underfunding drags productivity toward 0.5, collapsing the economy over ~10-20 rounds
- Episode ends only on: BANKRUPTCY, SHUTDOWN, MAX_ROUNDS, or PROSPERITY_THRESHOLD

**Pros:**
- No sudden death from one bad allocation
- Allows agents to learn from mistakes (RL-friendly)
- Voting remains meaningful: rejection hurts but doesn't kill instantly
- Abstention becomes a valid strategic choice (accept the productivity penalty to save treasury)

**Cons:**
- Removes the dramatic tension of the critical threshold
- May make the game too forgiving — agents can underfund for many rounds before collapsing
- Harder to define "success" when episodes run to max rounds with a slowly dying economy
- Productivity penalties compound in complex ways that are hard to tune

**Verdict:** Interesting for a "soft" variant, but loses the sharp edge that makes the game distinctive.

---

### Option E: Mandatory Proposals + Consensus-Only Voting ("Ceremonial" Model)

**Mechanic:**
- Remove abstention entirely (every minister MUST propose)
- Remove NO votes entirely (only YES/ABSTAIN)
- Or keep NO votes but make them purely symbolic (recorded but no effect)
- Debate phase becomes the **actual game**: ministers negotiate allocations in public
- Proposals reflect the negotiated consensus
- Voting rubber-stamps the agreement
- Critical check applies to all departments (since everyone proposed)
- If any proposal is below critical, episode ends

**Pros:**
- Pure truthfulness/cooperation mechanic — unique RL environment
- Aligns with user's insight that "debate should determine fair value for everyone"
- No death-by-rejection because rejection doesn't exist
- Models real-world consensus democracies where open deliberation, not secret ballots, drive decisions

**Cons:**
- Not really a "game" in the competitive sense
- No strategic tension in voting
- Hard to evaluate "good" vs. "bad" policy if there's no mechanism to block bad proposals
- May be too easy if agents always propose safely

**Verdict:** Too radical for the current design. Better suited as a separate game mode.

---

### Option F: Minimum Viable Treasury Guarantee

**Mechanic:**
- The treasury is **guaranteed** to always have at least `sum(Critical_d)` available for allocations
- Achieved by one of:
  - Baseline tax scales with population and always covers critical minimums
  - Treasury cannot be spent below `sum(Critical_d)` through discretionary allocations
  - A "reserve fund" is automatically set aside each round
- Critical check still applies but is only possible if a minister proposes below critical (which is their own fault)

**Pros:**
- Prevents unwinnable states
- Keeps existing proposal/voting mechanics mostly intact
- Maintains critical threshold as a meaningful floor

**Cons:**
- Artificial — removes the scarcity tension that makes the game interesting
- If baseline tax always covers critical, the game becomes too easy
- Hard to justify narratively why the treasury is magically protected

**Verdict:** Too much hand-holding. Undermines the core challenge.

---

## 4. Recommendation

**Option A (Auto-Fund Critical + Discretionary Proposals)** is recommended because it:

1. **Resolves all contradictions** without creating new dominant strategies
2. **Makes voting meaningful** — YES/NO is about growth, not life or death
3. **Incentivizes truthfulness** in debate — ministers can state needs honestly
4. **Preserves scarcity tension** — auto-critical is pure cost, so discretionary funding is essential
5. **Prevents unwinnable states** — if treasury < total critical, it's bankruptcy (a clear, existing condition)
6. **Aligns with the user's "ceremonial voting" insight** — the real negotiation is about discretionary surplus, not survival

The key insight is that **survival should not be negotiable**. The state guarantees minimum viable funding for all departments. What IS negotiable is how much extra each department gets to generate revenue and grow the economy. This makes the game about **cooperative investment under uncertainty**, not **who gets to survive**.

---

## 5. Open Questions for Deliberation

1. **Should ministers be allowed to propose 0 discretionary?** (i.e., "I only need the auto-critical this round")
   - Yes: gives ministers flexibility during crises
   - No: forces every department to always ask for something

2. **Should the auto-critical generate any revenue?**
   - Current spec: RF=0 at critical → revenue=0
   - Alternative: RF=0.2 at critical → small revenue to soften the bleed
   - Tradeoff: higher RF at critical makes the game easier but reduces the pressure to cooperate

3. **Should the shutdown condition be kept?**
   - If kept: redefine as `sum(Discretionary_d) = 0` for 2 rounds
   - If removed: game ends only on bankruptcy, max rounds, or prosperity threshold

4. **Should critical failure be completely removed, or kept as a sanity check?**
   - Under Option A, critical failure is impossible by design
   - Could keep it as a defensive check: "if auto-fund somehow fails, critical failure triggers"

5. **How does this interact with the direct-allocation shortcut (`_run_direct_allocation_round`)?**
   - Direct allocation currently checks all sectors for critical failure
   - Under Option A, direct allocation would need to split input into critical + discretionary, or auto-apply critical first

6. **Should we remove ABSTAIN_FROM_PROPOSAL entirely, or repurpose it?**
   - Remove: forces active participation every round
   - Repurpose: could become "ABSTAIN_FROM_DISCRETIONARY" (equivalent to proposing 0)

---

## 6. Implementation Estimate (if Option A is chosen)

| Component | Effort | Files |
|---|---|---|
| Auto-fund critical in game loop | Medium | `core/game.py` |
| Remove ABSTAIN_FROM_PROPOSAL | Low | `schemas/actions.py`, `schemas/phases.py`, `agents/` |
| Remove critical failure termination | Low | `core/game.py`, `core/reward.py`, `schemas/rewards.py` |
| Update shutdown condition | Low | `core/game.py` |
| Update all spec docs | Medium | `specification/*.md` |
| Update tests | Medium | `tests/unit/`, `tests/integration/` |
| Update agent adapters | Low | `agents/rule_based/`, `agents/llm/` |
| **Total** | **~1-2 days** | **~15 files** |

---

*This amendment is a living document. Options can be mixed, modified, or rejected based on deliberation.*
