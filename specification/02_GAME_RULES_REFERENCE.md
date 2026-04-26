# Game Rules Reference

Single-page anchor document defining all game mechanics using MUST/MUST NOT/MAY language.

---

## Agents / Ministers

- The game MUST have an even number of ministers: 4, 6, 8, or any other even integer
- Each minister MUST be assigned a distinct portfolio (department) at episode start
- Each minister MUST represent one department in the parliamentary simulation
- Ministers MUST act autonomously based on their assigned portfolio interests
- No minister MAY represent more than one department simultaneously
- Each minister MUST submit exactly one budget proposal every round during Phase 3 (amount MAY be zero)
- A minister MAY abstain from voting on any proposal (voting abstention remains distinct from proposal abstention, which is removed)

---

## Treasury & Budget

- The central treasury MUST be the sole source of funds for all department budgets
- Treasury baseline tax revenue MUST be set at episode initialization
- Treasury MUST receive productivity-based revenue from the previous round
- The treasury MAY NOT go into debt under any circumstances
- Any allocation that would cause treasury to go below zero MUST be rejected
- The treasury MUST be publicly observable by all ministers

---

## Budget Proposals

- Each minister MUST propose every round during Phase 3; there is no abstention from proposing
- A budget proposal MUST specify a **discretionary** amount (≥ 0): additional funding requested **above** the department’s auto-funded critical floor `Critical_d = Demand_d × 0.4`
- A proposal of **0** means the minister accepts only the automatic critical funding for that round (no extra discretionary spend)
- Proposals MUST be submitted sequentially during the proposal phase
- Proposals follow a rotating order that shifts each round (round-robin rotation)
- The starting department for round t is determined by `departments[t mod N]` where N is the number of departments
- Round 1 order: Social → Agriculture → Health → Education → Defense → Commerce
- Round 2 order: Agriculture → Health → Education → Defense → Commerce → Social
- Round 3 order: Health → Education → Defense → Commerce → Social → Agriculture
- This rotation prevents any department from having a permanent first-mover advantage
- A minister MAY propose zero (0) discretionary (auto-critical still applies in Phase 5)
- A minister MAY propose any **discretionary** amount up to the treasury **discretionary headroom**: `Treasury_balance - sum(Critical_d)` at submission time (validation uses remaining balance after reserving mandatory critical)
- A proposal MUST be publicly announced before voting begins
- No minister MAY propose a budget after the proposal phase has ended

---

## Voting

- All ministers MUST vote on each proposal unless they abstain
- A proposal MUST receive a majority of votes to be approved
- Majority MUST be defined as more than 50% of non-abstaining votes
- A tie in voting MUST result in the proposal being rejected
- All votes MUST be public and visible to all ministers
- A minister MAY vote YES, NO, or ABSTAIN on any proposal
- Abstaining ministers MUST NOT be counted toward the majority threshold calculation
- No minister MAY vote on a proposal they did not observe
- Ministers MUST abstain from voting on their own proposal
- Self-voting is prohibited to prevent conflict of interest

---

## Events

- Events MUST be generated at the start of each round with a defined probability
- Each event MUST have a severity level assigned at generation time
- Events MUST present a narrative description to all ministers
- Events MUST reveal severity level to all ministers
- Events MUST NOT reveal exact cost impact to ministers
- Ministers MAY infer event cost impact from severity and narrative
- Each event MUST be tagged with relevant department(s) affected
- Events that affect a department MUST scale that department's DEMAND by a multiplier
- Positive events inject cash directly into treasury
- Negative events increase the demand multiplier for affected sectors (making it harder to reach profit zone)

---

## Surplus & Rollover

- Unspent allocated budget MUST be returned to the central treasury at end of round
- Department surplus is NOT accumulated across rounds (no per-department rollover)
- Treasury-level surplus is tracked as total unspent allocation across all departments
- Departments consume `min(Allocation, Demand_d)` where `Demand_d = Baseline_d × (Population / Pop₀) × Event_Multiplier`
- Unspent allocation (`Allocation - Consumption`) returns to treasury automatically

## Bankruptcy

- The episode MUST end immediately if treasury reaches zero or less
- Bankruptcy occurs when `Treasury < sum(Consumption_d)` (can't pay for actual consumption)
- Bankruptcy also occurs when `sum(Allocation_d) > Treasury` at proposal time (can't approve budgets)
- Over-consumption (`Consumption > Allocation`) is IMPOSSIBLE by design: `Consumption = min(Allocation, Demand_d)`
- Under-funding (`Allocation < Demand_d`) causes reduced revenue but NOT bankruptcy

## Critical threshold & auto-critical funding (Option A)

- Each sector has a critical threshold `Critical_d = Demand_d × 0.4` (minimum viable operational floor)
- **Auto-critical (Phase 5, Step 0)**: Before any voted discretionary amounts are applied, every department receives `Critical_d` from the treasury unconditionally; that sum is debited first
- If `Treasury < sum(Critical_d)` at budget execution, the episode ends with **BANKRUPTCY** (not a separate “critical failure” termination)
- At allocation exactly equal to `Critical_d`, revenue factor is **0** (zero revenue from that department that round); auto-critical is treated as pure survival cost
- **Discretionary (Phase 3 proposals)**: Approved discretionary amounts are added on top of auto-critical; total allocation = `Critical_d + Discretionary_d`
- There is **no** episode termination solely because allocation is below critical—execution guarantees at least critical for every department whenever the treasury can afford it

## Shutdown

- The episode MUST end if `sum(Discretionary_d) = 0` for **2 consecutive rounds** (all approved discretionary amounts are zero). Because auto-critical is always funded when solvent, total allocation is not zero; shutdown tracks **discretionary** stagnation only
- Shutdown represents governance collapse where parliament approves no growth investment above survival baselines
- Shutdown is DISTINCT from bankruptcy: treasury may still be positive
- Shutdown does NOT trigger the -1000 bankruptcy penalty
- Shutdown condition is checked during Phase 9 (Termination Check)
- Episode terminates with status SHUTDOWN and reward = sum of rewards up to termination

---

## Revenue & Productivity

- Each sector's allocation is passed through a piecewise revenue function
- The function has 4 key points: Critical, Demand, Surplus, Wastage
- **Critical to Demand**: Revenue factor increases linearly from 0 to 1.0
- **Demand to Surplus**: Revenue factor increases linearly from 1.0 to 1.8 (PROFIT ZONE)
- **Surplus to Wastage**: Revenue factor decays exponentially from 1.8 to 1.0
- **Beyond Wastage**: Revenue factor continues decaying below 1.0 (loss)
- Revenue = Allocation × Revenue_Factor × Productivity
- Productivity is a persistent national variable bounded [0.5, 2.0]
- Productivity updates each round based on average revenue factor across all departments

---

## Example

- **Example**: Minister of Health proposes **20 discretionary** units (on top of auto-critical). Treasury holds 1000 units; total critical across departments is 190, so discretionary headroom is 810. The proposal is debated, voted on, and receives 3 YES votes, 1 NO vote, and 2 ABSTAIN votes from 6 ministers. Since 3 YES > 1 NO (majority of 4 non-abstaining votes), the proposal is approved. In Phase 5, auto-critical is funded first; then Health receives **critical + 20** total. Treasury is debited `sum(Critical_d)` plus approved discretionary. Revenue is computed on **total** allocation (critical + discretionary).