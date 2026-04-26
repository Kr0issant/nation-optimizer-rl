# 04 — Economy Model

> Defines the complete economic engine: treasury calculation, revenue generation, productivity system, population dynamics, and mandatory vs. discretionary budgeting (Option A).

---

## Starting Conditions

- **Initial Treasury**: 1000 units
- **Baseline Tax**: 100 units per round (constant, not tied to revenue)
- **Initial Population**: 1,000,000 (Pop₀)
- **Initial Productivity**: 1.0
- **Productivity Bounds**: [0.5, 2.0]
- **Number of Departments**: Set at episode initialization (v1: 6 departments)
- **v1 Department Baselines**:
  - Social/Municipal: 60
  - Agriculture: 70
  - Health: 90
  - Education/R&D: 80
  - Defense: 100
  - Commerce: 75

---

## Threshold Calculation

All thresholds scale with population and events. The four key thresholds are:

### Demand Threshold

- `Demand_d = Baseline_d × (Population_t / Pop₀) × Event_Multiplier`

Where:
- `Baseline_d` = fixed baseline per department
- `Population_t` = current population
- `Pop₀ = 1,000,000` (initial population)
- `Event_Multiplier` = sector-specific event multiplier from Event System

### Critical Threshold

- `Critical_d = Demand_d × 0.4`

This is the **mandatory survival floor** funded automatically in Phase 5 (Step 0) before discretionary proposals execute. It is not a separate episode termination concept: if the treasury cannot pay `sum(Critical_d)`, the episode ends with **BANKRUPTCY**.

### Surplus Threshold

- `Surplus_d = Demand_d × 1.5`

The peak profit zone. Revenue factor reaches 1.8 here.

### Wastage Threshold

- `Wastage_d = Demand_d × 2.5`

Revenue factor returns to 1.0 (break-even). Beyond this: exponential decay.

---

## Revenue Function (Piecewise)

The revenue factor determines how efficiently allocation converts to revenue.

### Revenue Factor Formula

```
         ⎧ None                           if x < Critical_d          (invalid / no revenue)
         ⎪
RF(x) =  ⎨ (x - Critical_d) / (Demand_d - Critical_d)   if Critical_d ≤ x < Demand_d
         ⎪
         ⎩ 1.0 + 0.8 × (x - Demand_d) / (Surplus_d - Demand_d)   if Demand_d ≤ x ≤ Surplus_d
         ⎪
         ⎩ 1.8 × exp(-k × (x - Surplus_d))   if x > Surplus_d

where k = ln(1.8) / (Wastage_d - Surplus_d)
```

### Revenue Factor Diagram

```
Revenue Factor (y)
    │
1.8 ┤        C ╭────╮
    │         ╱      ╲
1.0 ┤────────B        D────
    │       ╱          ╲
  0 ┤──────A            ╲
    │
    └──────┬────┬──────┬────→ Allocation (x)
         Critical Demand Surplus Wastage

A (Critical): Revenue factor = 0 at exactly Critical; below Critical is undefined / no revenue (should not occur after auto-critical in normal play)
B (Demand): Revenue factor = 1.0 (break-even)
C (Surplus): Revenue factor = 1.8 (peak profit)
D (Wastage): Revenue factor = 1.0 (break-even again)
```

### Segment Behavior

- **A→B (Critical to Demand)**: Linear growth from 0 to 1.0. Underfunded but survivable.
- **B→C (Demand to Surplus)**: Linear growth from 1.0 to 1.8. The profit zone.
- **C→D (Surplus to Wastage)**: Exponential decay from 1.8 to 1.0. Over-investment penalized.
- **D→∞ (Beyond Wastage)**: Exponential decay below 1.0. Severe penalty for waste.

### Revenue Factor Lookup Table

| Allocation (% of Demand) | Revenue Factor | Interpretation |
|--------------------------|----------------|-----------------|
| 0-39% | None / 0 RF | Below critical: no revenue in model; **Option A** funds at least critical when solvent |
| 40% | 0 | At critical threshold (zero revenue — survival cost only) |
| 50% | 0.25 | Linear segment mid-point |
| 100% | 1.0 | At demand (break-even) |
| 150% | 1.8 | At surplus (peak profit) |
| 250% | 1.0 | At wastage (break-even again) |
| 300%+ | <1.0 | Beyond wastage (loss) |

### Python Implementation

```python
import math

def revenue_factor(x, critical, demand, surplus, wastage):
    if x < critical:
        return None  # No revenue for sub-critical allocation (hypothetical if execution guarantees critical)
    elif x < demand:
        # Segment A→B: Linear from (critical, 0) to (demand, 1.0)
        return (x - critical) / (demand - critical)
    elif x <= surplus:
        # Segment B→C: Linear from (demand, 1.0) to (surplus, 1.8)
        t = (x - demand) / (surplus - demand)
        return 1.0 + 0.8 * t
    else:
        # Segment C→D→beyond: Exponential decay from (surplus, 1.8)
        k = math.log(1.8) / (wastage - surplus)
        return 1.8 * math.exp(-k * (x - surplus))
```

---

## Department Revenue

### Core Formula

- `Department_Revenue_d = Allocation_d × Revenue_Factor_d × Productivity_t`

Key difference from old model: Revenue is based on **allocation**, not consumption. A department receives revenue based on its budget allocation, multiplied by how efficiently that allocation is used.

### Revenue Calculation Algorithm

```python
def calculate_department_revenue(allocation, baseline, population, pop_0, event_multiplier, productivity):
    # Calculate thresholds
    demand = baseline * (population / pop_0) * event_multiplier
    critical = demand * 0.4
    surplus = demand * 1.5
    wastage = demand * 2.5
    
    # Calculate revenue factor
    rf = revenue_factor(allocation, critical, demand, surplus, wastage)
    
    if rf is None:
        return None  # No revenue (sub-critical allocation)
    
    # Calculate revenue (same round)
    revenue = allocation * rf * productivity
    
    return revenue
```

---

## Mandatory vs. discretionary budget (Option A)

### Mandatory (auto-critical)

- Each round in Phase 5 Step 0, every department receives `Critical_d` before discretionary is applied
- Debit: `sum(Critical_d)` from treasury
- Revenue factor at `Allocation = Critical_d` is **0** → **zero department revenue** from that slice (pure cost to treasury)

### Discretionary (Phase 3 proposals)

- Ministers request **additional** amounts ≥ 0 above `Critical_d`
- Voting approves or rejects **growth** funding; rejection implies `Discretionary_d = 0` but **not** `Allocation_d = 0`
- Total allocation: `Allocation_d = Critical_d + Discretionary_d`

### Affordability

- If treasury cannot cover `sum(Critical_d)` at the start of Phase 5 execution, the episode ends with **BANKRUPTCY**
- There is **no** `CRITICAL_FAILURE` termination reason in Option A

### Reference: RF vs allocation (given execution guarantees)

| Scenario | Allocation | Critical | RF | Notes |
|----------|------------|----------|-----|--------|
| At auto-critical only | Critical | Critical | 0 | No revenue |
| Between critical and demand | Between | Critical | 0–1 linear | Under-demand zone |
| At demand | Demand | Critical | 1.0 | Break-even |
| Profit zone | Demand–Surplus | Critical | 1.0–1.8 | Primary growth target |

---

## Persistent Productivity System

Productivity persists across rounds, creating long-term consequences for economic decisions.

### State Variable

- `Productivity_t = clamp(Productivity_{t-1} + ΔProductivity, 0.5, 2.0)`

Where:
- `Productivity_0 = 1.0` (initial at episode start)
- `Min_Productivity = 0.5`
- `Max_Productivity = 2.0`

### Delta Productivity

- `ΔProductivity = 0.05 × (Avg_Revenue_Factor - 1.0)`

Where:
- `Avg_Revenue_Factor = mean(Revenue_Factor_d for all departments)`

### Productivity Update Algorithm

```python
def update_productivity(previous_productivity, revenue_factors):
    avg_rf = sum(revenue_factors) / len(revenue_factors)
    delta = 0.05 * (avg_rf - 1.0)
    new_productivity = previous_productivity + delta
    return max(0.5, min(2.0, new_productivity))
```

### Productivity Behavior Table

| Avg Revenue Factor | Delta | Productivity Change | Interpretation |
|--------------------|-------|---------------------|----------------|
| 1.8 (peak) | +0.04 | Increases toward max | All sectors highly profitable |
| 1.5 | +0.025 | Moderate increase | Sectors moderately profitable |
| 1.0 | 0 | No change | Break-even state |
| 0.5 | -0.025 | Moderate decrease | Sectors at loss |
| 0.0 (critical) | -0.05 | Large decrease toward min | Sectors failing |

### Why Persistence Matters

- Small changes compound over 50 rounds
- A sustained profit zone (avg rf > 1.0) pushes productivity toward 2.0
- A sustained loss zone (avg rf < 1.0) pulls productivity toward 0.5
- Bounded to prevent runaway or collapse

---

## Population Dynamics

Population grows or shrinks based on productivity and crisis occurrence.

### Core Formula

- `Population_t = Population_{t-1} × (1 + Birth_Rate - Death_Rate)`

### Birth Rate

- `Birth_Rate = 0.005 × Productivity_t`

Where:
- Base birth rate = 0.005 (0.5% per round)
- Higher productivity leads to higher birth rate

### Death Rate

- `Death_Rate = 0.002 + Crisis_Penalty`

Where:
- Base death rate = 0.002 (0.2% per round)
- `Crisis_Penalty = 0.01` if critical event occurred in round t

### Population Update Algorithm

```python
def update_population(previous_population, productivity, crisis_occurred):
    base_birth = 0.005
    base_death = 0.002
    crisis_penalty = 0.01 if crisis_occurred else 0.0
    
    birth_rate = base_birth * productivity
    death_rate = base_death + crisis_penalty
    
    new_population = previous_population * (1 + birth_rate - death_rate)
    return round(new_population)
```

### Initial Conditions

- `Population_0 = 1,000,000`

---

## Treasury Calculation

Treasury updates at the end of each round based on allocations, revenues, and baseline tax.

### Treasury Update Formula

- `Treasury_t = Treasury_{t-1} + Baseline_Tax + Sum(Department_Revenues_t) - Sum(Allocation_d)`

Where:
- `Treasury_{t-1}` = treasury at end of previous round
- `Baseline_Tax = 100` (constant per round)
- `Sum(Department_Revenues_t)` = total revenue from all departments (same round)
- `Sum(Allocation_d)` = total budget allocated to all departments

### Treasury Flow

```
Round t starts:
  Treasury_t available for allocation

Round t allocation:
  Agents allocate to departments

Round t execution (same round):
  Each department generates Revenue based on Allocation × Revenue_Factor × Productivity

Round t end:
  Treasury_{t+1} = Treasury_t - sum(Allocation_d) + sum(Revenue_d) + Baseline_Tax
```

Key difference from old model: **Revenue applies same round as allocation**, not next round.

---

## Time Mapping

- **1 round = 3 months (1 quarter)**
- **50 rounds = 12.5 years** (full episode length)

### Display Format

- `Round t` → "Year X, Quarter Y"

Where:
- `Year = floor((t - 1) / 4) + 1`
- `Quarter = ((t - 1) % 4) + 1`

### Time Mapping Table

| Round | Year | Quarter |
|-------|------|---------|
| 1 | 1 | 1 |
| 2 | 1 | 2 |
| 3 | 1 | 3 |
| 4 | 1 | 4 |
| 5 | 2 | 1 |
| ... | ... | ... |
| 50 | 13 | 2 |

---

## Numerical Examples

### Example 1: Normal Operation at Demand

**Round 1 Setup:**
- Treasury = 1000
- Population = 1,000,000 (Pop₀)
- Productivity = 1.0
- 6 departments with exact demand allocation (no events)
- Allocations match demand exactly (100% of need)

**Threshold Calculation:**
- Demand_d = Baseline_d × (1,000,000 / 1,000,000) × 1.0 = Baseline_d
- Critical_d = Demand_d × 0.4 = Baseline_d × 0.4
- Surplus_d = Demand_d × 1.5 = Baseline_d × 1.5

**Department Allocations (v1):**
- Social: 60, Agriculture: 70, Health: 90, Education: 80, Defense: 100, Commerce: 75
- All at exactly 100% of demand

**Revenue Factor:**
- Each department at exactly demand: Revenue Factor = 1.0

**Department Revenues:**
- Social: 60 × 1.0 × 1.0 = 60
- Agriculture: 70 × 1.0 × 1.0 = 70
- Health: 90 × 1.0 × 1.0 = 90
- Education: 80 × 1.0 × 1.0 = 80
- Defense: 100 × 1.0 × 1.0 = 100
- Commerce: 75 × 1.0 × 1.0 = 75
- Total Revenue = 475

**Treasury Update:**
- Treasury_2 = 1000 + 100 + 475 - 475 = 1100

**Productivity Update:**
- Avg Revenue Factor = 1.0
- ΔProductivity = 0.05 × (1.0 - 1.0) = 0
- Productivity_2 = 1.0 (unchanged)

---

### Example 2: Over-Allocation to Surplus Zone

**Round 1 Setup:**
- Treasury = 1000
- Population = 1,000,000
- Productivity = 1.0
- Allocations at 150% of demand (surplus zone)

**All Department Allocations:**
- Social: 90 (150% of 60)
- Agriculture: 105 (150% of 70)
- Health: 135 (150% of 90)
- Education: 120 (150% of 80)
- Defense: 150 (150% of 100)
- Commerce: 112.5 (150% of 75)

**Revenue Factor at Surplus:**
- Each at 150% of demand: Revenue Factor = 1.8 (peak)

**Department Revenues:**
- Social: 90 × 1.8 × 1.0 = 162
- Agriculture: 105 × 1.8 × 1.0 = 189
- Health: 135 × 1.8 × 1.0 = 243
- Education: 120 × 1.8 × 1.0 = 216
- Defense: 150 × 1.8 × 1.0 = 270
- Commerce: 112.5 × 1.8 × 1.0 = 202.5
- Total Revenue = 1282.5

**Treasury Update:**
- Treasury_2 = 1000 + 100 + 1282.5 - 712.5 = 1670

**Productivity Update:**
- Avg Revenue Factor = 1.8
- ΔProductivity = 0.05 × (1.8 - 1.0) = 0.04
- Productivity_2 = 1.04

Note: Over-allocation to surplus zone generates 80% bonus revenue. Productivity increases slightly.

---

### Example 3: Critical Failure (Game Over)

**Round 1 Setup:**
- Treasury = 1000
- Population = 1,000,000
- Productivity = 1.0
- Defense allocation at 30% of demand (below critical)

**Defense Department:**
- Baseline = 100
- Demand = 100 × 1.0 = 100
- Critical = 100 × 0.4 = 40
- Allocation = 30 (30% of demand, below critical of 40)

**Critical Check:**
- Allocation (30) < Critical (40)
- **CRITICAL FAILURE**: Episode terminates immediately

**Final Prosperity Calculation:**
- Treasury at termination = 1000 (untouched if failure on allocation)
- Revenue generated before failure = 0 (no revenue because allocation failed)
- Final prosperity = (Treasury + Revenue) / Population = 1000 / 1,000,000 = 0.001

---

### Example 4: Under-Funding But Survivable

**Round 1 Setup:**
- Treasury = 1000
- Population = 1,000,000
- Productivity = 1.0
- Health allocation at 60% of demand

**Health Department:**
- Baseline = 90
- Demand = 90 × 1.0 = 90
- Critical = 90 × 0.4 = 36
- Allocation = 54 (60% of demand, above critical of 36)

**Revenue Factor (A→B segment):**
- Revenue Factor = (54 - 36) / (90 - 36) = 18 / 54 = 0.333

**Revenue:**
- Health Revenue = 54 × 0.333 × 1.0 = 18

Note: Under-funded departments generate reduced revenue. Below demand but above critical, revenue factor scales linearly from 0 to 1.0.

---

### Example 5: Population Dynamics with Productivity

**Round 1 Setup:**
- Population = 1,000,000
- Productivity = 1.0
- No crisis in Round 1

**Population Update:**
- Birth Rate = 0.005 × 1.0 = 0.005
- Death Rate = 0.002 + 0 = 0.002
- Net Growth = 0.005 - 0.002 = 0.003
- Population_2 = 1,000,000 × 1.003 = 1,003,000

**Round 2 Setup:**
- Productivity rises to 1.5 (from sustained profit)
- Crisis occurs in Round 2

**Population Update Round 2:**
- Birth Rate = 0.005 × 1.5 = 0.0075
- Death Rate = 0.002 + 0.01 = 0.012
- Net Growth = 0.0075 - 0.012 = -0.0045
- Population_3 = 1,003,000 × 0.9955 = 998,517

Note: Productivity boosts birth rate, but crisis penalty causes population decline even with good productivity.

---

### Example 6: Wastage Zone Penalty

**Round 1 Setup:**
- Treasury = 2000
- Population = 1,000,000
- Productivity = 1.0
- Commerce allocation at 300% of demand (beyond wastage)

**Commerce Department:**
- Baseline = 75
- Demand = 75 × 1.0 = 75
- Surplus = 75 × 1.5 = 112.5
- Wastage = 75 × 2.5 = 187.5
- Allocation = 225 (300% of demand)

**Revenue Factor (exponential decay):**
- k = ln(1.8) / (187.5 - 112.5) = 0.5878 / 75 = 0.007837
- x - surplus = 225 - 112.5 = 112.5
- Revenue Factor = 1.8 × exp(-0.007837 × 112.5) = 1.8 × 0.413 = 0.743

**Revenue:**
- Commerce Revenue = 225 × 0.743 × 1.0 = 167

Note: At 300% of demand (beyond wastage), revenue factor drops to 0.743. Over-allocation past wastage is heavily penalized compared to break-even at exactly 100%.

---

## Summary of Key Formulas

| Formula | Definition |
|---------|------------|
| `Demand_d` | `Baseline_d × (Population_t / Pop₀) × Event_Multiplier` |
| `Critical_d` | `Demand_d × 0.4` |
| `Surplus_d` | `Demand_d × 1.5` |
| `Wastage_d` | `Demand_d × 2.5` |
| `Revenue_Factor(x)` | Piecewise: None if x<Critical, linear to 1.0 at Demand, linear to 1.8 at Surplus, exponential decay beyond |
| `Department_Revenue_d` | `Allocation_d × Revenue_Factor_d × Productivity_t` |
| `Productivity_t` | `clamp(Productivity_{t-1} + 0.05 × (Avg_RF - 1.0), 0.5, 2.0)` |
| `Birth_Rate` | `0.005 × Productivity_t` |
| `Death_Rate` | `0.002 + Crisis_Penalty` |
| `Population_t` | `Population_{t-1} × (1 + Birth_Rate - Death_Rate)` |
| `Treasury_t` | `Treasury_{t-1} + Baseline_Tax + Sum(Revenues_t) - Sum(Allocations_d)` |

---

## Design Rationale

### Piecewise Revenue Curve

The four-point revenue curve creates distinct economic zones:
- **Profit zone** (demand to surplus): Rewards moderate over-investment
- **Loss zone** (critical to demand): Penalizes under-funding
- **Wastage zone** (beyond surplus): Penalizes excess allocation

This fundamentally differs from the old linear efficiency penalty. The economy now has strategic depth: agents must balance staying above demand (for profit) against avoiding waste (beyond wastage).

### Allocation-Based Revenue

Revenue based on **allocation**, not consumption. This simplifies the model and makes department performance directly tied to budget decisions rather than hidden consumption patterns.

### Persistent Productivity

Productivity persists round-to-round, creating path dependence. A sustained profit zone pushes productivity upward; a sustained loss zone pulls it downward. This rewards consistent good management and punishes sustained poor decisions.

### Same-Round Revenue

Revenue applied in the same round as allocation enables faster feedback loops. Agents see the results of their budget decisions immediately, rather than waiting a round for revenue to materialize.

### Population Scaling

Demand scales with population. As population grows, department needs grow proportionally. This keeps the model grounded: a larger population requires more resources across all sectors.

### Critical Threshold Game-Over

The 40% critical threshold creates a hard floor. Below this, the department (and by extension the nation) fails catastrophically. This forces agents to maintain minimum viable funding across all sectors.