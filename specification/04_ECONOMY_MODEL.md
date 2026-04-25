# 04 — Economy Model

> Defines the complete economic engine: treasury calculation, revenue generation, treasury surplus, and bankruptcy conditions.

---

## Starting Conditions

- **Initial Treasury**: 1000 units
- **Baseline Tax Revenue**: 100 units per round
- **Number of Departments**: Set at episode initialization (even number: 4, 6, 8, etc.)
- **Initial Department Efficiency Rating**: 1.0 for all departments
- **Initial Department Treasury Surplus**: 0 for all departments (treasury surplus is central, not department-level)
- **Baseline Consumption per Department** (v1):
  - Social/Municipal: 60
  - Agriculture: 70
  - Health: 90
  - Education/R&D: 80
  - Defense: 100
  - Commerce: 75

---

## Treasury Calculation

### Core Treasury Formula

At the start of each round t (after Phase 7 of round t-1), treasury is calculated as:

- `Treasury_t = Baseline_Tax_t + Productivity_Bonus_{t-1} + Sum(Department_Revenues_{t-1}) + Treasury_Return_{t-1}`

Where:
- `Baseline_Tax_t = 100 + 0.1 * Total_Revenue_{t-1}` (linked to economic activity)
- `Productivity_Bonus_{t-1}` is the productivity bonus from round t-1 (see Productivity Bonus formula)
- `Department_Revenues_{t-1}` is the sum of all department revenues from round t-1
- `Treasury_Return_{t-1} = sum(Allocation_{d,t-1} - Consumption_{d,t-1})` is the unspent allocation returned to treasury

Equivalently, treasury at end of round: `Treasury_{t+1} = Treasury_t - sum(Consumption_d) + Revenue_t`

---

## Department Need Calculation

Each department has a fixed baseline consumption plus any event-driven additional cost.

### Need Formula

- `Need_d = Baseline_Consumption_d + Event_Impact_d`

Where:
- `Baseline_Consumption_d`: fixed per department (e.g., Health: 90, Defense: 100)
- `Event_Impact_d`: additional cost from events affecting this department (hidden from agents)
- Agents only see severity level and narrative description, not the exact Event_Impact

### Consumption Formula

- `Consumption_d = min(Need_d, Allocation_d)`
- Cannot exceed allocation (no deficit spending)
- If `Need > Allocation`: underfunded consumption, department underperforms
- If `Need <= Allocation`: department functions fully

---

## Department Revenue Formula

Each department generates revenue based on its consumption, efficiency, and productivity.

### Department Revenue

- `Department_Revenue_d = Consumption_d * Efficiency_d * Productivity_Multiplier`

Where:
- `Consumption_d` = the amount actually consumed by department d in the previous round (output-based, not budget-based)
- `Efficiency_d` = the efficiency rating of department d (see below)
- `Productivity_Multiplier` = the global productivity multiplier (see below)

Rationale: Revenue comes from actual output (consumption), not budget size. A department that receives a large allocation but under-consumes (because it didn't need it) generates less revenue than one that fully utilizes its allocation.

### Efficiency

- `Efficiency_d = 1.0 - (|Allocation_d - Need_d| / Need_d)`

Where:
- If `Allocation_d = 0`, then `Efficiency_d = 0.0` (completely ignored)
- If `Allocation_d = Need_d`, then `Efficiency_d = 1.0` (perfect efficiency)
- If `Allocation_d > Need_d`, then `Efficiency_d < 1.0` (over-allocated, slight penalty)
- If `Allocation_d < Need_d`, then `Efficiency_d < 1.0` (underfunded, significant penalty)

Interpretation:
- Allocation = Need → Efficiency = 1.0 (perfect)
- Allocation > Need → Efficiency < 1.0 (waste - over-allocation penalized)
- Allocation < Need → Efficiency < 1.0 (underfunded - under-allocation penalized)
- Allocation = 0 → Efficiency = 0.0 (completely ignored)

### Global Productivity Multiplier

- `Productivity_Multiplier_t = 1.0 + (Investment_{t-1} / Total_Need_{t-1})`

Where:
- `Investment_{t-1} = sum(Consumption_{d,t-1})` = total actual spending across all departments (not savings, but consumption)
- `Total_Need_{t-1} = sum(Need_{d,t-1})` = total need across all departments in round t-1

This multiplier rewards system-wide productivity. Higher collective investment (actual consumption relative to need) increases the multiplier applied to all department revenues.

Rationale: Investment (actual spending on consumption) drives productivity, not savings. Treasury_Return is excluded here to avoid double-counting (Treasury_Return already appears in the treasury formula as a separate term).

---

## Productivity Bonus Formula

The productivity bonus rewards departments that consistently generate investment (actual consumption).

### Productivity Bonus (per department)

- `Productivity_Bonus_d = Investment * Efficiency_d * 0.3`

Where:
- `Investment = sum(Consumption_d)` = total actual spending across all departments (not per-department surplus)
- `Efficiency_d` = the efficiency rating of department d from round t-1
- `0.3` = a scaling factor to keep bonuses moderate relative to baseline tax

Note: Productivity bonus is based on total system investment (consumption across all departments), not per-department savings. Treasury_Return is NOT included here to avoid double-counting (Treasury_Return appears separately in the treasury formula).

### Total Productivity Bonus

- `Productivity_Bonus_{total} = Sum(Productivity_Bonus_d for all departments)`

---

## Treasury Return Mechanics

Unspent department allocations return to the central treasury at end of each round.

### Treasury Return Calculation

- `Treasury_Return = Sum(Allocation_d - Consumption_d for all departments)`

Where:
- `Allocation_d` = amount allocated to department d in round t
- `Consumption_d = min(Need_d, Allocation_d)` = amount actually spent by department d
- Positive values represent unspent budget returning to treasury

### Key rules:
- Unspent allocation from each department returns to the central treasury
- Treasury-level return is NOT distributed back to departments
- Treasury return is used to calculate the global productivity multiplier
- Under Model A, over-consumption is impossible (Consumption <= Allocation always)

### Under-Funding Handling

- Under Model A, if `Allocation_d < Need_d`, the department is underfunded
- `Consumption_d = Allocation_d` (cannot exceed allocation)
- Underfunding reduces the department's efficiency rating for the next round
- Underfunding does NOT cause bankruptcy (no deficit spending possible)

---

## Bankruptcy Conditions

Bankruptcy triggers immediate episode termination.

### Bankruptcy Triggers

The episode MUST end immediately when ANY of the following conditions are met:

1. **Treasury Bankruptcy**: `Treasury_t <= 0` at any point during round t
2. **Approval-time Bankruptcy**: `sum(Allocation_d) > Treasury` at proposal time (cannot approve all budgets)

### Model A Note: Consumption-Limited

Under Model A, `Consumption_d = min(Need_d, Allocation_d)`, so over-consumption is impossible by design.
Bankruptcy can only occur from treasury depletion (Phase 5), not from department-level deficit.

### Bankruptcy Check Timing

- Treasury bankruptcy is checked during Phase 5 (Budget Execution) and Phase 9 (Termination Check)
- Approval-time check occurs during Phase 4 (Voting) to prevent proposing budgets that can't be paid

---

## Population Growth

Population grows each round based on health conditions and crisis impacts.

### Population Formula

- `Population_t = Population_{t-1} * (1 + Growth_Rate_t)`

Where:
- `Growth_Rate_t = Base_Growth + Health_Bonus_t - Crisis_Penalty_t`
- `Base_Growth = 0.005` (0.5% per round, baseline demographic growth)
- `Health_Bonus_t = 0.002` if Health_Efficiency_t > 0.9, else `0` (population benefits from good health services)
- `Crisis_Penalty_t = 0.01` if a critical (severity 5) event occurred in round t, else `0` (crises cause population decline)

### Initial Population

- `Population_1 = 1000` (initial population at episode start)

### Population and Prosperity

Prosperity is now calculated as GDP per capita:

- `Prosperity_t = (Total_Revenue_t + Treasury_t) / Population_t`

A growing population is healthy but dilutes per-capita prosperity. Crises can cause population decline which increases per-capita prosperity even if total output falls.

### Population Growth Example

- Round 1: Population = 1000
- Round 2: Base growth only (Health_Efficiency <= 0.9, no crisis): Growth_Rate = 0.005, Population = 1000 * 1.005 = 1005
- Round 3: Good health (Health_Efficiency > 0.9), no crisis: Growth_Rate = 0.005 + 0.002 = 0.007, Population = 1005 * 1.007 = 1012.0
- Round 4: Crisis occurred (severity 5 event): Growth_Rate = 0.005 - 0.01 = -0.005, Population = 1012 * 0.995 = 1006.9

---

## Shutdown Conditions

Shutdown represents governance collapse where parliament cannot agree on any budget for two consecutive rounds.

### Shutdown Trigger

The episode MUST end immediately with status SHUTDOWN when:

- `sum(Allocation_{d,t}) = 0` AND `sum(Allocation_{d,t-1}) = 0`
- This means zero total allocation in the current round AND the previous round

### Shutdown vs Bankruptcy

| Aspect | Bankruptcy | Shutdown |
|--------|-----------|----------|
| Trigger | Treasury <= 0 or sum(Allocation) > Treasury | Zero allocation for 2 consecutive rounds |
| Type | Financial failure | Governance collapse |
| Treasury at trigger | Treasury <= 0 | Treasury may be positive |
| Penalty | -1000 | 0 (no penalty) |

### Shutdown Does Not Affect Treasury

- Shutdown is a governance failure, not a financial failure
- Treasury balance is unaffected by the Shutdown condition
- Shutdown check occurs during Phase 9 (Termination Check)

### Shutdown Check Timing

- Shutdown is checked during Phase 9 (Termination Check)
- Shutdown is checked BEFORE bankruptcy check

---

## Numerical Examples

### Example 1: Normal Operation with Investment-Based Productivity

**Round 1 Setup:**
- Treasury = 1000 (initial)
- 6 departments: Social (Baseline=60), Agriculture (Baseline=70), Health (Baseline=90), Education (Baseline=80), Defense (Baseline=100), Commerce (Baseline=75)
- Population = 1000
- Allocations: Social=60, Agriculture=70, Health=90, Education=80, Defense=100, Commerce=75 (all match Need exactly)
- Total allocation = 475 units
- No events in this round

**Round 1 Execution:**
- Each department Need = Baseline_Consumption + Event_Impact = Baseline
- Social: Need=60, Allocation=60, Consumption=min(60,60)=60
- Agriculture: Need=70, Allocation=70, Consumption=min(70,70)=70
- Health: Need=90, Allocation=90, Consumption=min(90,90)=90
- Education: Need=80, Allocation=80, Consumption=min(80,80)=80
- Defense: Need=100, Allocation=100, Consumption=min(100,100)=100
- Commerce: Need=75, Allocation=75, Consumption=min(75,75)=75

**Treasury Return:** 0 (perfect allocation, no waste)

**Investment Calculation:**
- Investment = sum(Consumption) = 60 + 70 + 90 + 80 + 100 + 75 = 475
- Total Need = 475
- Productivity_Multiplier = 1.0 + (475/475) = 2.0

**Revenue Calculation (Phase 7):**
- All departments: Efficiency = 1.0 - (|60-60|/60) = 1.0 (perfect)
- Department Revenue = Consumption * Efficiency * Productivity_Multiplier
- Social Revenue = 60 * 1.0 * 2.0 = 120
- Agriculture Revenue = 70 * 1.0 * 2.0 = 140
- Health Revenue = 90 * 1.0 * 2.0 = 180
- Education Revenue = 80 * 1.0 * 2.0 = 160
- Defense Revenue = 100 * 1.0 * 2.0 = 200
- Commerce Revenue = 75 * 1.0 * 2.0 = 150
- Total Department Revenue = 950

**Productivity Bonus:**
- Productivity_Bonus_d = Investment * Efficiency_d * 0.3 = 475 * 1.0 * 0.3 = 142.5 per efficient department
- Total Productivity Bonus = 6 * 142.5 = 855

**Round 2 Treasury (at start of round):**
- Baseline_Tax_2 = 100 + 0.1 * Total_Revenue_1 = 100 + 0.1 * 950 = 195
- Treasury_2 = Baseline_Tax_2 + Productivity_Bonus_1 + Total_Department_Revenue_1 + Treasury_Return_1
- Treasury_2 = 195 + 855 + 950 + 0 = 2000

Note: Perfect efficiency generates high revenue and productivity multiplier of 2.0. The system rewards accurate allocation matching need exactly.

---

### Example 2: Over-Allocation Penalty

**Round 1 Setup:**
- Treasury = 1000
- 4 departments: Health (Baseline=90), Education (Baseline=80), Defense (Baseline=100), Social (Baseline=60)
- Allocations: Health=200, Education=150, Defense=150, Social=120 (all over-allocated)
- Total allocation = 620 units
- No events

**Round 1 Consumption:**
- Health: Need=90, Allocation=200, Consumption=min(90,200)=90, unspent=110
- Education: Need=80, Allocation=150, Consumption=min(80,150)=80, unspent=70
- Defense: Need=100, Allocation=150, Consumption=min(100,150)=100, unspent=50
- Social: Need=60, Allocation=120, Consumption=min(60,120)=60, unspent=60

**Treasury Return:** 110 + 70 + 50 + 60 = 290

**Investment Calculation:**
- Investment = sum(Consumption) = 90 + 80 + 100 + 60 = 330
- Total Need = 90 + 80 + 100 + 60 = 330
- Productivity_Multiplier = 1.0 + (330/330) = 2.0

**Revenue Calculation:**
- Health Efficiency = 1.0 - (|200-90|/90) = 1.0 - 1.22 = -0.22 (over-allocated!)
- Education Efficiency = 1.0 - (|150-80|/80) = 1.0 - 0.875 = 0.125
- Defense Efficiency = 1.0 - (|150-100|/100) = 1.0 - 0.5 = 0.5
- Social Efficiency = 1.0 - (|120-60|/60) = 1.0 - 1.0 = 0.0

Department Revenues:
- Health Revenue = 90 * (-0.22) * 2.0 = -39.6 (negative revenue!)
- Education Revenue = 80 * 0.125 * 2.0 = 20
- Defense Revenue = 100 * 0.5 * 2.0 = 100
- Social Revenue = 60 * 0.0 * 2.0 = 0

Total Department Revenue = 80.4

**Round 2 Treasury:**
- Baseline_Tax_2 = 100 + 0.1 * 80.4 = 108
- Treasury_2 = 108 + 0 + 80.4 + 290 = 478.4

Note: Over-allocation is heavily penalized. Health allocated 200 but only needed 90, resulting in negative efficiency and negative revenue. Social allocated 120 but only needed 60, resulting in zero efficiency and zero revenue.

---

### Example 3: Under-Funding During Crisis

**Round 1 Setup:**
- Treasury = 1000
- 4 departments: Health (Baseline=90), Education (Baseline=80), Defense (Baseline=100), Social (Baseline=60)
- War event increases Defense Need to 200
- Allocations: Health=90, Education=80, Defense=150, Social=60 (Defense under-funded)
- Total allocation = 380 units

**Round 1 Consumption:**
- Health: Need=90, Allocation=90, Consumption=90
- Education: Need=80, Allocation=80, Consumption=80
- Defense: Need=200, Allocation=150, Consumption=150 (under-funded)
- Social: Need=60, Allocation=60, Consumption=60

**Treasury Return:** 0 (all allocations fully consumed)

**Investment Calculation:**
- Investment = 90 + 80 + 150 + 60 = 380
- Total Need = 90 + 80 + 200 + 60 = 430
- Productivity_Multiplier = 1.0 + (380/430) = 1.88

**Revenue Calculation:**
- Health Efficiency = 1.0 - (|90-90|/90) = 1.0
- Education Efficiency = 1.0 - (|80-80|/80) = 1.0
- Defense Efficiency = 1.0 - (|150-200|/200) = 1.0 - 0.25 = 0.75 (penalized for under-funding)
- Social Efficiency = 1.0 - (|60-60|/60) = 1.0

Department Revenues:
- Health Revenue = 90 * 1.0 * 1.88 = 169.2
- Education Revenue = 80 * 1.0 * 1.88 = 150.4
- Defense Revenue = 150 * 0.75 * 1.88 = 211.5
- Social Revenue = 60 * 1.0 * 1.88 = 112.8

Total Department Revenue = 643.9

**Round 2 Treasury:**
- Baseline_Tax_2 = 100 + 0.1 * 643.9 = 164.4
- Treasury_2 = 164.4 + 0 + 643.9 + 0 = 808.3

Note: Defense was under-funded during crisis (allocated 150, needed 200), resulting in reduced efficiency (0.75). However, the crisis caused high investment relative to need, so productivity multiplier remains high (1.88).

---

### Example 4: Population Growth and Prosperity

**Round 1 Setup:**
- Treasury = 1000
- Population = 1000
- Total Revenue = 500 (hypothetical)
- Treasury Balance = 800

**Prosperity Calculation:**
- Prosperity = (Total_Revenue + Treasury) / Population = (500 + 800) / 1000 = 1.3

**Round 2 Population:**
- No crisis, Health_Efficiency <= 0.9
- Growth_Rate = 0.005 (base only)
- Population_2 = 1000 * 1.005 = 1005

**Round 3 Population (with good health):**
- Health_Efficiency > 0.9, no crisis
- Growth_Rate = 0.005 + 0.002 = 0.007
- Population_3 = 1005 * 1.007 = 1012.0

**Round 4 Population (crisis):**
- Critical event occurred (severity 5)
- Growth_Rate = 0.005 - 0.01 = -0.005
- Population_4 = 1012 * 0.995 = 1006.9

Note: Crisis causes population decline even though base growth is positive. Population growth dilutes per-capita prosperity.

---

### Example 5: Black Swan Event

**Round 1 Setup:**
- Treasury = 2000
- 6 departments, all efficiently allocated
- Financial Collapse event (severity 5, Base_Cost=200)

**Event Impact:**
- All departments impacted: Event_Impact_d = 200 * 5 * 1.0 = 1000 each
- Total Need across all departments = baseline + event impact

**Revenue Impact:**
- High event costs reduce consumption efficiency across the board
- Productivity multiplier drops due to reduced investment relative to need

Note: Black swan events are rare (0.5% chance) but devastating. They impact all departments simultaneously with severity 5.

---

## Summary of Key Formulas

| Formula | Definition |
|---------|------------|
| `Need_d` | `Baseline_Consumption_d + Event_Impact_d` |
| `Consumption_d` | `min(Need_d, Allocation_d)` |
| `Investment` | `sum(Consumption_d)` (total actual spending) |
| `Treasury_t` | `Baseline_Tax_t + Productivity_Bonus_{t-1} + Sum(Department_Revenues_{t-1}) + Treasury_Return_{t-1}` |
| `Baseline_Tax_t` | `100 + 0.1 * Total_Revenue_{t-1}` |
| `Department_Revenue_d` | `Consumption_d * Efficiency_d * Productivity_Multiplier` |
| `Efficiency_d` | `1.0 - (|Allocation_d - Need_d| / Need_d)` |
| `Productivity_Multiplier_t` | `1.0 + (Investment_{t-1} / Total_Need_{t-1})` |
| `Productivity_Bonus_d` | `Investment * Efficiency_d * 0.3` |
| `Treasury_Return` | `Sum(Allocation_d - Consumption_d)` (unspent returned to treasury) |
| `Population_t` | `Population_{t-1} * (1 + Growth_Rate_t)` |
| `Growth_Rate_t` | `0.005 + Health_Bonus_t - Crisis_Penalty_t` |
| `Prosperity_t` | `(Total_Revenue_t + Treasury_t) / Population_t` |
| `Bankruptcy` | `Treasury_t <= 0 OR sum(Allocation_d) > Treasury` |

---

## Design Rationale

- **Model A (Government Budget Execution)**: Treasury only pays for actual consumption, not full allocations. Unspent allocation returns to treasury automatically.
- Revenue is calculated AFTER consumption to create a feedback loop: efficient departments generate more revenue next round
- Efficiency Rating uses consumption efficiency to reward accurate budgeting (allocation close to need)
- Global Productivity Multiplier incentivizes system-wide efficiency over individual department performance
- Treasury-level return pooling incentivizes accurate budgeting (departments don't over-request since unspent returns to central treasury)
- Model A prevents deficit spending: `Consumption = min(Need, Allocation)`, so over-consumption is impossible by design
- Baseline Tax ensures treasury never fully depletes even if all departments perform poorly
