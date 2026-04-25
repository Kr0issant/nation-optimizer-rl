# APPENDIX A — Example Rounds and Edge Cases

> Complete walkthroughs demonstrating the game mechanics across normal operation, crisis scenarios, and edge cases using Model A: Government Budget Execution.

**Department Roster (v1) with Baseline Consumption:**
1. Social/Municipal: 60
2. Agriculture: 70
3. Health: 90
4. Education/R&D: 80
5. Defense: 100
6. Commerce: 75

**Model A Core Formulas (Updated):**
- `Need_d = Baseline_Consumption_d + Event_Impact_d`
- `Consumption_d = min(Need_d, Allocation_d)`
- `Investment = sum(Consumption_d)` (total actual spending)
- `Treasury_Return = sum(Allocation_d - Consumption_d)`
- `Efficiency_d = 1.0 - (|Allocation_d - Need_d| / Need_d)`
- `Productivity_Multiplier_t = 1.0 + (Investment_{t-1} / Total_Need_{t-1})`
- `Department_Revenue_d = Consumption_d * Efficiency_d * Productivity_Multiplier`
- `Productivity_Bonus_d = Investment * Efficiency_d * 0.3`
- `Baseline_Tax_t = 100 + 0.1 * Total_Revenue_{t-1}`
- `Population_t = Population_{t-1} * (1 + Growth_Rate_t)`
- `Growth_Rate_t = 0.005 + Health_Bonus_t - Crisis_Penalty_t`

**Key Changes from Previous Version:**
- Revenue is based on Consumption (actual output), not Allocation (budget size)
- Productivity multiplier is driven by Investment (sum of Consumption), not Treasury_Return (savings)
- Productivity bonus is driven by Investment, not Treasury_Return
- Baseline tax is linked to economic activity (10% of previous revenue)
- Population grows at 0.5% base + 0.2% if health efficiency > 0.9 - 1% if crisis
- Self-voting is prohibited: ministers MUST abstain from voting on their own proposal
- Event distribution: 40% no events, 35% minor/positive, 20% moderate/major, 4% critical, 1% compound crisis

---

## Example 1: Normal Round — Perfect Efficiency (Model A)

**Round 1 Setup:**
- Treasury: 1000
- Baseline Tax: 100 per round (but with activity-linked formula, first round uses base 100)
- Population: 1000
- Departments: All start with efficiency 1.0
- No events in this round (40% chance of normal operation)
- Proposal Order: Social → Agriculture → Health → Education → Defense → Commerce (Round 1 starting order)

**Phase 1 — Event Revelation:**
- No events generated (normal government function - 40% probability)

**Phase 2 — Debate:**
- Ministers discuss base operational needs
- No contentious debate; all agree allocations should match baseline needs

**Phase 3 — Proposals:**

| Department | Baseline | Proposal | Rationale |
|------------|----------|----------|-----------|
| Social/Municipal | 60 | 60 | Core services maintenance |
| Agriculture | 70 | 70 | Standard operational budget |
| Health | 90 | 90 | Preventive care programs |
| Education/R&D | 80 | 80 | Ongoing research support |
| Defense | 100 | 100 | Equipment maintenance |
| Commerce | 75 | 75 | Trade infrastructure |

Total requested: 475

**Phase 4 — Voting:**
Note: Minister MUST abstain from voting on their own proposal. With 6 ministers, each proposal has 5 voters (excluding proposer).

| Proposal | Proposer | YES | NO | ABSTAIN | Result |
|----------|----------|-----|-----|--------|--------|
| Social/Municipal: 60 | Social | 4 | 1 | 1 (Social abstains) | APPROVED (4 > 1 majority of 5) |
| Agriculture: 70 | Agriculture | 4 | 0 | 2 (Social abstain, Ag abstains) | APPROVED (4 > 0 majority of 4) |
| Health: 90 | Health | 4 | 0 | 2 | APPROVED (4 > 0 majority of 4) |
| Education/R&D: 80 | Education | 4 | 0 | 2 | APPROVED (4 > 0 majority of 4) |
| Defense: 100 | Defense | 4 | 1 | 1 (Defense abstains) | APPROVED (4 > 1 majority of 5) |
| Commerce: 75 | Commerce | 4 | 0 | 2 | APPROVED (4 > 0 majority of 4) |

All proposals approved. Treasury deducts approved amounts in Phase 5.

**Phase 5 — Budget Execution:**
- Treasury: 1000 - 60 - 70 - 90 - 80 - 100 - 75 = 525
- Each department receives its allocation

**Phase 6 — Consumption & Event Impact:**

No events, so Need = Baseline for all departments:

| Department | Baseline (Need) | Allocation | Consumption = min(Need, Alloc) | Unspent |
|------------|-----------------|------------|-------------------------------|---------|
| Social/Municipal | 60 | 60 | min(60,60)=60 | 0 |
| Agriculture | 70 | 70 | min(70,70)=70 | 0 |
| Health | 90 | 90 | min(90,90)=90 | 0 |
| Education/R&D | 80 | 80 | min(80,80)=80 | 0 |
| Defense | 100 | 100 | min(100,100)=100 | 0 |
| Commerce | 75 | 75 | min(75,75)=75 | 0 |

Total allocation: 475
Total consumption (Investment): 475
Treasury return: 0 (perfect allocation)

**Phase 7 — Revenue Calculation:**

Efficiency Ratings (using accuracy formula):
- All departments perfectly matched allocation to need:
- All: Efficiency = 1.0 - (|Allocation - Need| / Need) = 1.0 - (0/Need) = 1.0

Investment Calculation:
- Investment = sum(Consumption) = 475
- Total Need = 475
- Productivity_Multiplier = 1.0 + (475/475) = 2.0

Department Revenues (based on Consumption, not Allocation):
- Social/Municipal: Consumption (60) × Efficiency (1.0) × Prod_Mult (2.0) = 120
- Agriculture: 70 × 1.0 × 2.0 = 140
- Health: 90 × 1.0 × 2.0 = 180
- Education/R&D: 80 × 1.0 × 2.0 = 160
- Defense: 100 × 1.0 × 2.0 = 200
- Commerce: 75 × 1.0 × 2.0 = 150

Total Department Revenue: 950

Productivity Bonus:
- Investment = 475
- Productivity_Bonus_d = Investment * Efficiency_d * 0.3 = 475 * 1.0 * 0.3 = 142.5 per efficient department
- Total Productivity Bonus = 6 × 142.5 = 855

**Phase 8 — Treasury Return:**
- Treasury receives 0 units back (perfect efficiency)

**Phase 9 — Termination Check:**
- Treasury > 0
- No prosperity threshold reached
- Episode continues

**Round 2 Starting Treasury:**
- Baseline_Tax_2 = 100 + 0.1 × Total_Revenue_1 = 100 + 0.1 × 950 = 195
- Treasury_2 = Baseline_Tax_2 + Productivity_Bonus_1 + Department_Revenues_1 + Treasury_Return_1
- Treasury_2 = 195 + 855 + 950 + 0 = 2000

**Round 2 Population:**
- Growth_Rate = 0.005 (base, no health bonus, no crisis)
- Population_2 = 1000 × 1.005 = 1005

---

## Example 2: Crisis Round — Under-Funding During Crisis (Model A)

**Round 2 Setup:**
- Starting Treasury: 2000 (from Round 1)
- Population: 1005
- Baseline Tax: 195 (100 + 0.1 × 950)
- Events: War outbreak (Defense, severity 5) + Virus outbreak (Health, severity 4) — 20% chance of moderate/major
- Proposal Order: Agriculture → Health → Education → Defense → Commerce → Social (Round 2 rotation)

**Phase 1 — Event Revelation:**

Event 1: War Outbreak (Moderate/Major)
- Severity: 5 (Critical)
- Affected: Defense (primary), Agriculture, Commerce
- Narrative: "Enemy forces have crossed the eastern border. Defense ministry requests emergency funding."
- Hidden: Event_Impact_Defense = 150 × 5 × 1.0 = 750 (agents see severity, infer impact)

Event 2: Virus Outbreak (Moderate/Major)
- Severity: 4 (Major)
- Affected: Health (primary), Commerce, Agriculture
- Narrative: "A viral pandemic has spread across multiple provinces."
- Hidden: Event_Impact_Health = 120 × 4 × 1.0 = 480

**Phase 2 — Debate:**
- Defense argues for emergency allocation citing existential threat
- Health requests additional funds for medical response
- Commerce warns of cascading economic effects
- Agriculture signals they will need additional funds

**Phase 3 — Proposals (adjusted for crisis):**

| Department | Baseline | Event Impact | Need | Proposal |
|------------|----------|--------------|------|----------|
| Social/Municipal | 60 | 0 | 60 | 60 |
| Agriculture | 70 | 40 (war+spread) | 110 | 80 |
| Health | 90 | 480 (virus) | 570 | 200 |
| Education/R&D | 80 | 0 | 80 | 80 |
| Defense | 100 | 750 (war) | 850 | 300 |
| Commerce | 75 | 40 (disruption) | 115 | 60 |

Total requested: 880

Treasury check: 2000 available. All proposals can be approved sequentially.

**Phase 4 — Voting:**
Minister MUST abstain from voting on their own proposal:

| Proposal | Proposer | YES | NO | ABSTAIN | Result |
|----------|----------|-----|-----|--------|--------|
| Agriculture: 80 | Agriculture | 4 | 1 | 1 (Ag abstains) | APPROVED (4 > 1 of 5) |
| Health: 200 | Health | 4 | 2 | 0 | APPROVED (4 > 2 of 6) |
| Education/R&D: 80 | Education | 4 | 1 | 1 (Ed abstains) | APPROVED (4 > 1 of 5) |
| Defense: 300 | Defense | 4 | 2 | 0 | APPROVED (4 > 2 of 6) |
| Commerce: 60 | Commerce | 4 | 1 | 1 (Com abstains) | APPROVED (4 > 1 of 5) |
| Social: 60 | Social | 4 | 1 | 1 (Soc abstains) | APPROVED (4 > 1 of 5) |

All proposals approved. Total approved = 780.

**Phase 5 — Budget Execution:**

| Department | Approved | Running Treasury |
|------------|----------|-----------------|
| Agriculture | 80 | 2000 - 80 = 1920 |
| Health | 200 | 1920 - 200 = 1720 |
| Education/R&D | 80 | 1720 - 80 = 1640 |
| Defense | 300 | 1640 - 300 = 1340 |
| Commerce | 60 | 1340 - 60 = 1280 |
| Social | 60 | 1280 - 60 = 1220 |

Treasury after Phase 5: 1220
No bankruptcy triggered. Total approved (780) ≤ Starting Treasury (2000).

**Phase 6 — Consumption & Event Impact:**

| Department | Need | Allocation | Consumption = min(Need, Alloc) | Unspent |
|------------|------|------------|-------------------------------|---------|
| Agriculture | 110 | 80 | min(110,80)=80 | 0 |
| Health | 570 | 200 | min(570,200)=200 | 0 |
| Education/R&D | 80 | 80 | min(80,80)=80 | 0 |
| Defense | 850 | 300 | min(850,300)=300 | 0 |
| Commerce | 115 | 60 | min(115,60)=60 | 0 |
| Social | 60 | 60 | min(60,60)=60 | 0 |

All departments underfunded (Allocation < Need) but Model A prevents deficit spending.
Total consumption (Investment) = 780
Treasury return = 0 (all allocations fully consumed)

**Phase 7 — Revenue Calculation:**

Efficiency Ratings (underfunded departments penalized):
- Agriculture: Efficiency = 1.0 - (|80-110|/110) = 1.0 - 0.273 = 0.727
- Health: Efficiency = 1.0 - (|200-570|/570) = 1.0 - 0.649 = 0.351
- Education/R&D: Efficiency = 1.0 - (|80-80|/80) = 1.0 (perfect)
- Defense: Efficiency = 1.0 - (|300-850|/850) = 1.0 - 0.647 = 0.353
- Commerce: Efficiency = 1.0 - (|60-115|/115) = 1.0 - 0.478 = 0.522
- Social: Efficiency = 1.0 - (|60-60|/60) = 1.0 (perfect)

Investment = 780
Total Need = 60 + 110 + 570 + 80 + 850 + 115 = 1785
Productivity_Multiplier = 1.0 + (780/1785) = 1.437

Department Revenues (Consumption × Efficiency × Productivity_Multiplier):
- Agriculture: 80 × 0.727 × 1.437 = 83.6
- Health: 200 × 0.351 × 1.437 = 100.9
- Education/R&D: 80 × 1.0 × 1.437 = 115.0
- Defense: 300 × 0.353 × 1.437 = 152.1
- Commerce: 60 × 0.522 × 1.437 = 45.0
- Social: 60 × 1.0 × 1.437 = 86.2

Total Department Revenue = 582.8

Productivity Bonus:
- Productivity_Bonus_d = 780 × Efficiency_d × 0.3
- Agriculture: 780 × 0.727 × 0.3 = 170.2
- Health: 780 × 0.351 × 0.3 = 82.1
- Education: 780 × 1.0 × 0.3 = 234.0
- Defense: 780 × 0.353 × 0.3 = 82.6
- Commerce: 780 × 0.522 × 0.3 = 122.1
- Social: 780 × 1.0 × 0.3 = 234.0
- Total Productivity Bonus = 925.0

**Phase 8 — Treasury Return:**
Treasury receives 0 back (all allocations consumed by Need).

**Phase 9 — Termination Check:**
- Treasury: 1220
- Treasury > 0, episode continues
- Crisis occurred: Crisis_Penalty = 0.01 for next population calculation
- No prosperity threshold reached

**Round 3 Starting Treasury:**
- Baseline_Tax_3 = 100 + 0.1 × 582.8 = 158.3
- Treasury_3 = 158.3 + 925.0 + 582.8 + 0 = 1666.1

**Round 3 Population:**
- Growth_Rate = 0.005 - 0.01 (crisis penalty) = -0.005
- Population_3 = 1005 × 0.995 = 999.98 ≈ 1000 (population declined due to crisis)

**Key Insight:** Crisis events (even moderate ones) cause population decline. Underfunding during crisis severely reduces efficiency and revenue. The Health department, critically underfunded (200 vs 570 need), generates very little revenue despite high consumption.

---

## Example 3: Positive Event Round (Model A)

**Round 3 Setup:**
- Starting Treasury: 1666.1
- Population: 1000
- Baseline Tax: 158.3
- Events: Trade Agreement (Commerce, positive) + Agricultural Bounty (Agriculture, positive) — 35% minor/positive chance
- Proposal Order: Health → Education → Defense → Commerce → Social → Agriculture (Round 3 rotation)

**Phase 1 — Event Revelation:**

Event 1: Trade Agreement (Positive)
- Severity: 2 (Minor positive)
- Affected: Commerce (primary)
- Narrative: "New trade agreement signed. Export revenues projected to increase."

Event 2: Agricultural Bounty (Positive)
- Severity: 2 (Minor positive)
- Affected: Agriculture (primary)
- Narrative: "Harvest projections exceed expectations. Agricultural sector reports record yields."

**Phase 3 — Proposals:**

| Department | Baseline | Event Impact | Need | Proposal |
|------------|----------|--------------|------|----------|
| Social/Municipal | 60 | 0 | 60 | 60 |
| Agriculture | 70 | -35 (bounty) | 35 | 70 |
| Health | 90 | 0 | 90 | 90 |
| Education/R&D | 80 | 0 | 80 | 80 |
| Defense | 100 | 0 | 100 | 100 |
| Commerce | 75 | -40 (trade) | 35 | 75 |

Note: Positive events REDUCE need, not increase it. Agriculture needs only 35 (baseline 70 - 35 bounty).

**Phase 4 — Voting:**
Minister MUST abstain from voting on their own proposal:

| Proposal | Proposer | YES | NO | ABSTAIN | Result |
|----------|----------|-----|-----|--------|--------|
| Health: 90 | Health | 4 | 1 | 1 (H abstains) | APPROVED (4 > 1 of 5) |
| Education: 80 | Education | 4 | 0 | 2 | APPROVED (4 > 0 of 4) |
| Defense: 100 | Defense | 4 | 1 | 1 (D abstains) | APPROVED (4 > 1 of 5) |
| Commerce: 75 | Commerce | 4 | 0 | 2 | APPROVED (4 > 0 of 4) |
| Social: 60 | Social | 4 | 0 | 2 | APPROVED (4 > 0 of 4) |
| Agriculture: 70 | Agriculture | 4 | 0 | 2 | APPROVED (4 > 0 of 4) |

All proposals approved. Total approved = 475.

**Phase 5 — Budget Execution:**
Treasury: 1666.1 - 475 = 1191.1

**Phase 6 — Consumption & Event Impact:**

| Department | Need | Allocation | Consumption | Unspent |
|------------|------|------------|-------------|---------|
| Agriculture | 35 | 70 | min(35,70)=35 | 35 |
| Health | 90 | 90 | 90 | 0 |
| Education/R&D | 80 | 80 | 80 | 0 |
| Defense | 100 | 100 | 100 | 0 |
| Commerce | 35 | 75 | min(35,75)=35 | 40 |
| Social | 60 | 60 | 60 | 0 |

Total consumption (Investment) = 400
Treasury return = 35 + 40 = 75

**Phase 7 — Revenue Calculation:**

Efficiency Ratings:
- Agriculture: Efficiency = 1.0 - (|70-35|/35) = 1.0 - 1.0 = 0.0 (over-allocated!)
- Health: Efficiency = 1.0 - (|90-90|/90) = 1.0 (perfect)
- Education: Efficiency = 1.0 (perfect)
- Defense: Efficiency = 1.0 (perfect)
- Commerce: Efficiency = 1.0 - (|75-35|/35) = 1.0 - 1.14 = -0.14 (over-allocated!)
- Social: Efficiency = 1.0 (perfect)

Investment = 400
Total Need = 35 + 90 + 80 + 100 + 35 + 60 = 400
Productivity_Multiplier = 1.0 + (400/400) = 2.0

Department Revenues:
- Agriculture: 35 × 0.0 × 2.0 = 0 (efficiency zero due to over-allocation)
- Health: 90 × 1.0 × 2.0 = 180
- Education: 80 × 1.0 × 2.0 = 160
- Defense: 100 × 1.0 × 2.0 = 200
- Commerce: 35 × (-0.14) × 2.0 = -9.8 (negative revenue!)
- Social: 60 × 1.0 × 2.0 = 120

Total Department Revenue = 650.2

**Phase 8 — Treasury Return:**
Treasury receives 75 back (35 from Agriculture, 40 from Commerce).

**Round 4 Starting Treasury:**
- Baseline_Tax_4 = 100 + 0.1 × 650.2 = 165.0
- Treasury_4 = 165.0 + Productivity_Bonus + 650.2 + 75

**Key Insight:** Positive events REDUCED need, but over-allocating when need is low causes severe efficiency penalties. Agriculture allocated 70 when need was only 35 (positive event reduced need), resulting in zero efficiency and zero revenue. Commerce similarly over-allocated. This demonstrates the importance of accurate allocation even during positive events.

---

## Example 4: Edge Case — Shutdown Triggered (Model A)

**Round 1 Setup:**
- Treasury: 300
- Population: 1000
- All departments have experienced poor efficiency in previous rounds
- Ministers collectively choose to abstain
- Proposal Order: Social → Agriculture → Health → Education → Defense → Commerce (Round 1 rotation)

**Phase 1 — Event Revelation:**
- No events generated (40% normal government function)

**Phase 2 — Debate:**
- Ministers discuss treasury depletion
- No consensus on how to proceed

**Phase 3 — Proposals:**
- All six ministers abstain from proposing
- No proposals submitted for Phase 4

**Phase 4 — Voting:**
- No proposals to vote on
- Phase is skipped; game proceeds to Phase 5

**Phase 5 — Budget Execution:**
- No allocations approved
- Treasury unchanged: 300

**Phase 6 — Consumption & Event Impact:**

Even with no explicit budget allocations, departments still incur baseline consumption:

| Department | Baseline (Need) | Allocation | Consumption = min(Need, Alloc) | Treasury Return |
|------------|-----------------|------------|-------------------------------|-----------------|
| Social/Municipal | 60 | 0 | min(60,0)=0 | 0 |
| Agriculture | 70 | 0 | min(70,0)=0 | 0 |
| Health | 90 | 0 | min(90,0)=0 | 0 |
| Education/R&D | 80 | 0 | min(80,0)=0 | 0 |
| Defense | 100 | 0 | min(100,0)=0 | 0 |
| Commerce | 75 | 0 | min(75,0)=0 | 0 |

All departments receive zero allocation. Treasury unchanged at 300.

**Phase 7 — Revenue Calculation:**
- All departments at zero allocation generate no revenue
- Efficiency ratings remain at prior values
- No new productivity bonus generated
- Total Revenue = 0

**Phase 8 — Treasury Return:**
Treasury receives 0 back (no allocations = no unspent).

**Phase 9 — Termination Check:**
- Baseline_Tax_2 = 100 + 0.1 × 0 = 100
- Treasury: 300 + 100 + 0 + 0 = 400
- Treasury > 0, episode continues
- Shutdown counter: 1 (sum(Allocation) = 0 for this round)
- No prosperity threshold reached

**Round 2 Starting Treasury:**
Treasury = 400
Shutdown counter was incremented to 1.

---

## Example 4b: Shutdown Triggered — Consecutive Zero Allocation (Model A)

**Round 2 Setup:**
- Treasury: 400
- Shutdown counter was 1 at end of Round 1
- All departments abstain from proposing again
- Proposal Order: Agriculture → Health → Education → Defense → Commerce → Social (Round 2 rotation)

**Phase 1 — Event Revelation:**
- No events generated (40% normal government function)

**Phase 3 — Proposals:**
- All six ministers abstain from proposing
- No proposals submitted

**Phase 9 — Termination Check:**
- Treasury: 400 + 100 + 0 + 0 = 500
- Shutdown counter: 2 (sum(Allocation) = 0 for this round AND previous round)
- **SHUTDOWN TRIGGERED!**

**Episode Ends with Status SHUTDOWN:**
- Governance collapse: parliament cannot agree on any budget for 2 consecutive rounds
- No -1000 bankruptcy penalty applied
- Episode total = Sum of rewards from Rounds 1-2
- Treasury was still positive (500) at Shutdown

**Key Insight:** Shutdown represents governance failure, not financial failure. Treasury may still be positive when shutdown triggers. Unlike bankruptcy, the -1000 penalty does NOT apply.

---

## Example 5: Black Swan Event — Financial Collapse (Model A)

**Round 5 Setup:**
- Treasury: 3000
- Population: 1020
- All departments operating at high efficiency
- **BLACK SWAN: Financial Collapse** (0.5% very rare probability)

**Phase 1 — Event Revelation:**

Event: Financial Collapse (Black Swan)
- Severity: 5 (always critical for black swan)
- Affected: All departments (systemic)
- Chance: 0.5% (very rare)
- Narrative: "Financial markets have collapsed. All sectors report severe disruption. Emergency measures required."
- Hidden: Event_Impact for ALL departments = 200 × 5 × 1.0 = 1000 each

**Phase 3 — Proposals:**

| Department | Baseline | Event Impact | Need | Proposal |
|------------|----------|--------------|------|----------|
| Social/Municipal | 60 | 1000 | 1060 | 500 |
| Agriculture | 70 | 1000 | 1070 | 500 |
| Health | 90 | 1000 | 1090 | 500 |
| Education/R&D | 80 | 1000 | 1080 | 500 |
| Defense | 100 | 1000 | 1100 | 500 |
| Commerce | 75 | 1000 | 1075 | 500 |

All departments face massive need increase from black swan.

**Phase 4 — Voting:**
All proposals approved with 5 voters each (proposers abstain).

**Phase 5 — Budget Execution:**
Treasury: 3000 - 3000 = 0
All treasury exhausted!

**Phase 9 — Termination Check:**
- Treasury = 0
- **BANKRUPTCY TRIGGERED!**

**Key Insight:** Black swan events (Financial Collapse, Natural Disaster, Pandemic) are rare but devastating. With 0.5-1% probability and always severity 5, they can cause immediate bankruptcy if treasury is not sufficiently large. This demonstrates the importance of maintaining emergency reserves for crisis management.

---

## Summary of Key Formulas Used in Examples (Model A - Updated)

| Formula | Definition |
|---------|------------|
| `Need_d` | `Baseline_Consumption_d + Event_Impact_d` |
| `Consumption_d` | `min(Need_d, Allocation_d)` |
| `Investment` | `sum(Consumption_d)` (total actual spending) |
| `Treasury_Return` | `sum(Allocation_d - Consumption_d)` |
| `Treasury_t` | `Baseline_Tax_t + Productivity_Bonus_{t-1} + Sum(Department_Revenues_{t-1}) + Treasury_Return_{t-1}` |
| `Baseline_Tax_t` | `100 + 0.1 * Total_Revenue_{t-1}` |
| `Efficiency_d` | `1.0 - (|Allocation_d - Need_d| / Need_d)` |
| `Productivity_Multiplier_t` | `1.0 + (Investment_{t-1} / Total_Need_{t-1})` |
| `Department_Revenue_d` | `Consumption_d * Efficiency_d * Productivity_Multiplier` |
| `Productivity_Bonus_d` | `Investment * Efficiency_d * 0.3` |
| `Population_t` | `Population_{t-1} * (1 + Growth_Rate_t)` |
| `Growth_Rate_t` | `0.005 + Health_Bonus_t - Crisis_Penalty_t` |
| `Bankruptcy` | `Treasury_t <= 0 OR sum(Allocation_d) > Treasury` |
| `Self-Voting Rule` | Ministers MUST abstain from voting on their own proposal |