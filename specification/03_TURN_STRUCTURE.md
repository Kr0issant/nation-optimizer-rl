# 03 TURN STRUCTURE

> Defines the exact phase-by-phase flow of a single game turn/round.

## Time Mapping

- **1 round = 3 months (1 quarter)**
- **50 rounds = 12.5 years** (full episode span)
- **Display format to agents**: "Year X, Quarter Y"
  - Year = `(round - 1) // 4 + 1`
  - Quarter = `(round - 1) % 4 + 1`
- Time progression is tracked and displayed but does not otherwise affect mechanics

## Phase Ordering Summary

```
1. Event Revelation Phase
2. Debate/Discussion Phase
3. Budget Proposal Phase
4. Voting Phase
5. Budget Execution Phase
6. Consumption & Event Impact Phase
7. Revenue Calculation Phase
8. Surplus Rollover Phase
9. Termination Check Phase
```

## Phase 1: Event Revelation Phase

**Purpose**: Reveal all events for the current round to all ministers.

**Execution Order**:
- The event system generates 1-N events for the round (see Event System)
- Each event is presented with:
  - Narrative description (what happened)
  - Severity level (e.g., Low, Medium, High, Critical)
  - Department relevancy (which ministries are affected)
- Agents do NOT see exact cost impact at this stage
- Agents must infer potential impact on their departments

**Treasury Note**: No treasury change occurs in this phase.

## Phase 2: Debate/Discussion Phase

**Purpose**: Allow ministers to discuss events, share concerns, and signal priorities before proposals.

**Execution Order**:
- Ministers may exchange messages publicly (see Guardrails for communication restrictions)
- Discussion occurs before any budget proposals are made
- Ministers can:
  - Share interpretations of event impact
  - Signal budget priorities
  - Form alliances or coalitional positions
- Discussion is optional (game proceeds if all ministers skip)

**Treasury Note**: No treasury change occurs in this phase.

## Phase 3: Budget Proposal Phase

**Purpose**: Each minister proposes **discretionary** additional funding for their department (above the auto-funded critical floor).

**Execution Order**:
- Ministers propose in rotating order (round-robin), not random order
- The starting department for round t is `departments[t mod N]` where N = number of departments
- Department order: [Social, Agriculture, Health, Education, Defense, Commerce]
- Round 1: Social → Agriculture → Health → Education → Defense → Commerce
- Round 2: Agriculture → Health → Education → Defense → Commerce → Social
- Round 3: Health → Education → Defense → Commerce → Social → Agriculture
- This rotation shifts each round, preventing any department from having permanent first-mover advantage
- Each minister MUST submit exactly one proposal:
  - Department identifier
  - **Discretionary** amount ≥ 0 (extra funding requested above `Critical_d`; **0** means “critical only”)
- Proposals are public (all ministers see each proposal as it occurs)
- **Abstention from proposing is removed** — every minister must actively submit (including `amount: 0`)
- Treasury remains unchanged until Phase 5

**Treasury Note**: Treasury is NOT debited during this phase. Proposals are promises only. Valid discretionary amounts are capped by discretionary headroom (`Treasury - sum(Critical_d)`), not raw treasury alone.

## Phase 4: Voting Phase

**Purpose**: Ministers vote on each proposal in the order submitted.

**Execution Order**:
- For each proposal (in submission order):
  - Minister who proposed MUST abstain from voting on their own proposal (vote is invalid if cast)
  - All other ministers vote: Yes, No, or Abstain
  - Votes are public (all ministers see who voted what)
  - Simple majority (>50% of non-abstaining votes) required for approval
  - Tie votes: proposal is rejected (see Voting Protocol for tie-breaking)
- Voting continues until all proposals have been voted upon
- Abstentions count toward quorum but do not influence vote outcome

**Treasury Note**: No treasury change occurs in this phase.

## Phase 5: Budget Execution Phase

**Purpose**: Apply **auto-critical** funding for all departments, then execute **approved discretionary** proposals on top. Debiting follows mandatory-first, then discretionary.

**Step 0 — Auto-fund critical (mandatory)**:
- For each department: set baseline allocation to `Critical_d = Demand_d × 0.4`
- Debit `sum(Critical_d)` from treasury unconditionally
- If `Treasury < sum(Critical_d)` **before** this debit: episode ends with **BANKRUPTCY** (Phase 5 immediate termination path)
- Revenue factor at exactly `Critical_d` is **0** (no revenue from that department this round from the critical slice)

**Step 1 — Approved discretionary**:
- For each proposal with status APPROVED: add `Discretionary_d` (the proposed amount) to that department’s allocation
- Debit the treasury for each approved discretionary amount (sequential depletion: later approvals see reduced remaining balance during vote tally / ordering)
- **Rejected** proposals: department keeps **only** auto-critical (`Allocation_d = Critical_d`); no discretionary debit for that department
- Total allocation: `Allocation_d = Critical_d + Discretionary_d` (with `Discretionary_d = 0` if rejected or if proposal amount was 0)

**Execution Order**:
1. Auto-fund critical for all departments (or BANKRUPTCY if unaffordable)
2. Apply approved discretionary on top; handle rejections as “critical only”
3. Proceed to Phase 6 with final allocations

**Treasury Note**: Total Phase 5 debit = `sum(Critical_d) + sum(approved Discretionary_d)`. There is **no** separate `CRITICAL_FAILURE` termination; unaffordable mandatory critical is **BANKRUPTCY**.

## Phase 6: Consumption & Event Impact Phase

**Purpose**: Departments consume their budgets based on Need; events apply their costs.

**Execution Order**:
- Each department's Need is calculated: `Need_d = Baseline_Consumption_d + Event_Impact_d`
- Each department consumes: `Consumption_d = min(Need_d, Allocation_d)`
- Event impact is applied here (affects Need, which is hidden from agents)
- If `Allocation_d < Need_d`: department is underfunded, consumption equals allocation
- If `Allocation_d >= Need_d`: department functions fully, consumption equals Need
- Departments may have leftover surplus if allocation > consumption

**Treasury Note**: Treasury is NOT directly affected in this phase. Consumption is bounded by allocation (no deficit spending).

## Phase 7: Revenue Calculation Phase

**Purpose**: Calculate revenue generated by each department and credit treasury immediately.

**Execution Order**:
- Revenue is calculated based on how efficiently each department used its allocation
- Department revenue formula: `Department_Revenue_d = Allocation_d × Revenue_Factor_d × Productivity`
- Revenue_Factor_d is determined by the piecewise efficiency curve (see Economy Model)
- Departments in deficit generate reduced revenue based on shortfall
- Treasury is credited IMMEDIATELY with `sum(Department_Revenue_d)`

**Treasury Formula** (same-round, after Phase 5 debits):
```
Treasury_after_Revenue = Treasury_before_Phase5 - sum(Allocation_d) + sum(Department_Revenue_d)
```
where `sum(Allocation_d)` includes both auto-critical and discretionary components.

**Key Point**: Revenue applies in the SAME ROUND it is generated. There is no "next round" delay.

## Phase 8: Treasury Surplus Phase

**Purpose**: Return unspent department allocations to the central treasury (after revenue has been added).

**Execution Order**:
- For each department: `Treasury_Return_d = Allocation_d - Consumption_d`
- Total `Treasury_Return = sum(Treasury_Return_d) = sum(Allocation_d - Consumption_d)`
- Treasury is credited with `Treasury_Return`
- No per-department surplus accumulation occurs
- Treasury_Return represents the unspent allocation returning to treasury

**Treasury Note**: Treasury is credited with total unspent allocation in this phase. This is the only surplus mechanism. Net effect after Phase 7 and Phase 8: Treasury only pays for actual consumption minus net revenue generated (`sum(Consumption_d) - sum(Department_Revenue_d)`).

## Phase 9: Termination Check Phase

**Purpose**: Determine if the episode continues or ends. Update persistent state.

**Time Update**:
- Increment round counter
- Display format: "Year X, Quarter Y" where Year = `(round - 1) // 4 + 1`, Quarter = `(round - 1) % 4 + 1`

**State Updates**:
- Update persistent productivity: `Productivity_t = clamp(Productivity_{t-1} + 0.05 × (Avg_RF - 1.0), 0.5, 2.0)`
  - Avg_RF = average Revenue_Factor across all departments
  - Productivity increases when Avg_RF > 1.0, decreases when Avg_RF < 1.0
  - Productivity is clamped to [0.5, 2.0] range
- Update population: `Population_t = Population_{t-1} × (1 + Birth_Rate - Death_Rate)`
  - Birth_Rate and Death_Rate depend on department performance and events

**Shutdown Counter**: A counter tracks consecutive rounds with **zero total discretionary** approved spend.
- Shutdown counter increments when `sum(Discretionary_d) = 0` (all departments’ approved discretionary amounts are 0)
- Shutdown counter resets to 0 when `sum(Discretionary_d) > 0`
- If Shutdown counter >= 2, episode terminates with status SHUTDOWN
- Note: Auto-critical is always positive when solvent, so `sum(Allocation_d) = 0` is not used for shutdown under Option A

**Execution Order**:
1. Update time display
2. Update productivity and population
3. Check shutdown condition: if Shutdown counter >= 2, episode ends (governance collapse)
4. Check bankruptcy condition: if treasury <= 0, episode ends (failure)
5. Check max rounds condition: if round >= max_rounds, episode ends (evaluate success)
6. Check prosperity threshold: if prosperity >= target, episode ends (success)
7. If any termination condition is met:
   - Final state is recorded
   - Reward is calculated
   - Episode concludes
8. If no termination condition is met:
   - Proceed to next round's Phase 1

**Shutdown Note**: Shutdown is checked BEFORE bankruptcy. Shutdown represents governance stagnation (no approved discretionary growth for two consecutive rounds), not financial failure. Treasury may still be positive when Shutdown triggers.

**Treasury Note**: Final treasury state is recorded at this point.

## Treasury Timing Summary

| Phase | Treasury Debit | Treasury Credit |
|-------|---------------|-----------------|
| 1. Event Revelation | No | No |
| 2. Debate/Discussion | No | No |
| 3. Budget Proposal | No | No |
| 4. Voting | No | No |
| 5. Budget Execution | Yes (`sum(Critical_d)` + approved discretionary) | No |
| 6. Consumption & Event Impact | No | No |
| 7. Revenue Calculation | No | Yes (same-round revenue credited immediately) |
| 8. Treasury Surplus | No | Yes (unspent allocation returns) |
| 9. Termination Check | No | No |

**Net Treasury Change per Round**:
```
Treasury_delta = sum(Department_Revenue_d) - sum(Consumption_d)
```
The flow is:
- Phase 5: Treasury -= sum(Allocation_d) [allocations committed]
- Phase 7: Treasury += sum(Department_Revenue_d) [revenue credited same round]
- Phase 8: Treasury += sum(Allocation_d - Consumption_d) [unspent returned]
- Net: Treasury -= sum(Consumption_d) + sum(Allocation_d - Consumption_d) - sum(Department_Revenue_d) = Treasury -= sum(Consumption_d) - sum(Department_Revenue_d)

Equivalent formula: Treasury only pays for actual consumption minus revenue generated.

## Critical Design Notes

**Events BEFORE Proposals**: Events are revealed in Phase 1, before any budget proposals in Phase 3. This ensures agents must infer event impact when formulating their asks. Agents see narrative + severity but NOT exact cost, creating the uncertainty that drives learning.

**Same-Round Revenue**: Revenue is calculated and credited to treasury in the same round it is generated. A department's allocation in round T is offset by revenue that same department generates in round T. This creates an immediate feedback loop between allocation, consumption, and revenue.

**Revenue from Productivity**: Revenue is multiplied by the persistent Productivity factor. Higher productivity means better revenue generation from the same allocation, creating an incentive for efficient spending.

**Auto-critical first**: Mandatory critical funding is applied before discretionary execution so every department has a survival floor when the treasury can afford it; revenue is then computed on the **total** allocation (critical + discretionary).

**Productivity and Population Updates**: These persistent state variables are only updated in Phase 9, after all financial transactions for the round are complete. This ensures that productivity changes only affect the NEXT round's revenue calculation.
