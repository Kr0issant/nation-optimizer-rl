# Game Rules Reference

Single-page anchor document defining all game mechanics using MUST/MUST NOT/MAY language.

---

## Agents / Ministers

- The game MUST have an even number of ministers: 4, 6, 8, or any other even integer
- Each minister MUST be assigned a distinct portfolio (department) at episode start
- Each minister MUST represent one department in the parliamentary simulation
- Ministers MUST act autonomously based on their assigned portfolio interests
- No minister MAY represent more than one department simultaneously
- A minister MAY abstain from proposing a budget for their own department in any round
- A minister MAY abstain from voting on any proposal, including their own

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

- Each minister MUST be able to propose a budget allocation for their own department
- A budget proposal MUST specify an exact amount requested from the treasury
- Proposals MUST be submitted sequentially during the proposal phase
- Proposals follow a rotating order that shifts each round (round-robin rotation)
- The starting department for round t is determined by `departments[t mod N]` where N is the number of departments
- Round 1 order: Social → Agriculture → Health → Education → Defense → Commerce
- Round 2 order: Agriculture → Health → Education → Defense → Commerce → Social
- Round 3 order: Health → Education → Defense → Commerce → Social → Agriculture
- This rotation prevents any department from having a permanent first-mover advantage
- A minister MAY propose zero (0) as their budget request
- A minister MAY propose any amount up to and including the current treasury balance
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
- Events that affect a department MUST impact that department's revenue or costs

---

## Surplus & Rollover

- Unspent allocated budget MUST be returned to the central treasury at end of round
- Department surplus is NOT accumulated across rounds (no per-department rollover)
- Treasury-level surplus is tracked as total unspent allocation across all departments
- Departments consume `min(Need, Allocation)` where `Need = Baseline_Consumption + Event_Impact`
- Unspent allocation (`Allocation - Consumption`) returns to treasury automatically
- Efficiency bonus MAY be applied when department operates efficiently (Allocation close to Need)
- Efficiency bonus MUST be calculated based on accuracy formula: `Efficiency_d = 1.0 - (|Allocation_d - Need_d| / Need_d)`
- Efficiency = 1.0 when Allocation = Need; decreases when Allocation differs from Need in either direction

## Bankruptcy

- The episode MUST end immediately if treasury reaches zero or less
- Bankruptcy occurs when `Treasury < sum(Consumption_d)` (can't pay for actual consumption)
- Bankruptcy also occurs when `sum(Allocation_d) > Treasury` at proposal time (can't approve budgets)
- Over-consumption (`Consumption > Allocation`) is IMPOSSIBLE by design: `Consumption = min(Need, Allocation)`
- Under-funding (`Allocation < Need`) causes department underperformance but NOT bankruptcy
- Bankruptcy condition MUST be checked after Phase 5 (Budget Execution) and Phase 8 (Treasury Surplus)

## Shutdown

- The episode MUST end immediately if `sum(Allocation_d) = 0` for 2 consecutive rounds
- Shutdown represents governance collapse where parliament cannot agree on any budget
- Shutdown is DISTINCT from bankruptcy: treasury may still be positive
- Shutdown does NOT trigger the -1000 bankruptcy penalty
- Shutdown condition is checked during Phase 9 (Termination Check)
- Episode terminates with status SHUTDOWN and reward = sum of rewards up to termination

---

## Revenue & Productivity

- Each department MAY generate revenue based on its efficiency rating
- Department efficiency rating MUST be calculated from past surplus/under-spend events
- Revenue generated by departments MUST flow into the central treasury
- A baseline productivity multiplier MUST be applied to all department revenues
- Productivity of the previous round MUST affect the treasury baseline for the next round
- A department MAY have zero revenue if it performed inefficiently in prior rounds

---

## Example

- **Example**: Minister of Health proposes 300 units for healthcare. Treasury currently holds 1000 units. The proposal is debated, voted on, and receives 3 YES votes, 1 NO vote, and 2 ABSTAIN votes from 6 ministers. Since 3 YES > 1 NO (majority of 4 non-abstaining votes), the proposal is approved. Treasury is reduced to 700 units. At end of round, Health's Need is 250 (Baseline_Consumption 200 + Event_Impact 50), so Health consumes `min(250, 300) = 250` units. The 50 units unspent (300 - 250) return to the central treasury as treasury-level surplus.