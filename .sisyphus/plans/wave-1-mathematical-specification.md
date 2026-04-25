# Wave 1 Mathematical Specification: Revenue Function & Productivity System

> **Purpose**: This document defines the EXACT mathematical formulas for the reconciliation. All subsequent document rewrites (Wave 2+) MUST use these formulas verbatim. No interpretation needed — implement directly from this spec.

**Status**: FINAL (no TBD, no ambiguity)

---

## PART A: Piecewise Revenue Function

### 4 Key Points of the Revenue Curve

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
```

| Point | Name | x (Allocation) | y (Revenue Factor) |
|-------|------|----------------|---------------------|
| A | Critical | `x = Critical_d` | `y = 0` |
| B | Demand | `x = Demand_d` | `y = 1.0` |
| C | Surplus | `x = Surplus_d` | `y = 1.8` |
| D | Wastage | `x = Wastage_d` | `y = 1.0` |

### Derived Thresholds

```
Critical_d = Demand_d × 0.4
Demand_d = Baseline_d × (Population_t / Pop₀) × Event_Multiplier
Surplus_d = Demand_d × 1.5
Wastage_d = Demand_d × 2.5
```

Where:
- `Pop₀ = 1,000,000` (initial population)
- `Event_Multiplier` = sector-specific event multiplier (see Event System)

### Revenue Factor Function (Python)

```python
import math

def revenue_factor(x, critical, demand, surplus, wastage):
    """
    Calculate revenue factor for a given allocation.
    
    Args:
        x: Allocation amount
        critical: Critical threshold (below = game over)
        demand: Demand threshold (revenue factor = 1.0)
        surplus: Surplus threshold (revenue factor = 1.8, peak)
        wastage: Wastage threshold (revenue factor returns to 1.0)
    
    Returns:
        float: Revenue factor in range [0, 1.8], or None if critical failure
    """
    if x < critical:
        return None  # CRITICAL FAILURE: episode terminates
    elif x < demand:
        # Segment A→B: Linear interpolation from (critical, 0) to (demand, 1.0)
        slope = 1.0 / (demand - critical)
        return slope * (x - critical)
    elif x <= surplus:
        # Segment B→C: Linear interpolation from (demand, 1.0) to (surplus, 1.8)
        t = (x - demand) / (surplus - demand)
        return 1.0 + 0.8 * t
    else:
        # Segment C→D→beyond: Exponential decay from (surplus, 1.8)
        # At wastage: y = 1.0
        # Solve for k: 1.8 * exp(-k * (wastage - surplus)) = 1.0
        # k = ln(1.8) / (wastage - surplus)
        k = math.log(1.8) / (wastage - surplus)
        return 1.8 * math.exp(-k * (x - surplus))
```

### Revenue Factor Function (Mathematical)

For a given sector with allocation `x`:

```
         ⎧ None                           if x < Critical_d          (CRITICAL FAILURE)
         ⎪
RF(x) =  ⎨ (x - Critical_d) / (Demand_d - Critical_d)   if Critical_d ≤ x < Demand_d
         ⎪
         ⎩ 1.0 + 0.8 × (x - Demand_d) / (Surplus_d - Demand_d)   if Demand_d ≤ x ≤ Surplus_d
         ⎪
         ⎩ 1.8 × exp(-k × (x - Surplus_d))   if x > Surplus_d

where k = ln(1.8) / (Wastage_d - Surplus_d)
```

### Segment Verification

| Segment | Range | Start Point | End Point | Behavior |
|---------|-------|-------------|-----------|----------|
| A→B | Critical ≤ x < Demand | (Critical, 0) | (Demand, 1.0) | Linear growth |
| B→C | Demand ≤ x ≤ Surplus | (Demand, 1.0) | (Surplus, 1.8) | Linear growth to peak |
| C→D | Surplus < x ≤ Wastage | (Surplus, 1.8) | (Wastage, 1.0) | Exponential decay |
| D→∞ | x > Wastage | (Wastage, 1.0) | (∞, 0) | Exponential decay below 1.0 |

### Mathematical Verification at Key Points

1. **At x = Critical_d**:
   - x < critical: return None (CRITICAL FAILURE)

2. **At x = Demand_d**:
   - Second case: (Demand_d - Critical_d) / (Demand_d - Critical_d) = 1.0 ✓

3. **At x = Surplus_d**:
   - Third case: 1.0 + 0.8 × (Surplus_d - Demand_d) / (Surplus_d - Demand_d) = 1.0 + 0.8 = 1.8 ✓

4. **At x = Wastage_d**:
   - Fourth case: 1.8 × exp(-k × (Wastage_d - Surplus_d)) = 1.8 × exp(-ln(1.8)) = 1.8 / 1.8 = 1.0 ✓

5. **For x > Wastage_d**:
   - Fourth case: 1.8 × exp(-k × (x - Surplus_d)) < 1.0 ✓ (below break-even)

---

## PART B: Department Revenue Formula

### Core Formula

```
Department_Revenue_d = Allocation_d × Revenue_Factor_d × Productivity_t
```

**Key difference from current spec**: Revenue is based on ALLOCATION (not consumption).

### Revenue Calculation Algorithm

```python
def calculate_department_revenue(allocation, baseline, population, pop_0, event_multiplier, productivity):
    """
    Calculate revenue for a department.
    
    Args:
        allocation: Budget allocated to department
        baseline: Baseline consumption need
        population: Current population
        pop_0: Initial population (1,000,000)
        event_multiplier: Event-driven demand multiplier
        productivity: Current productivity factor
    
    Returns:
        tuple: (revenue, revenue_factor, critical_threshold, demand_threshold, surplus_threshold, wastage_threshold)
    """
    # Calculate thresholds
    demand = baseline * (population / pop_0) * event_multiplier
    critical = demand * 0.4
    surplus = demand * 1.5
    wastage = demand * 2.5
    
    # Calculate revenue factor
    rf = revenue_factor(allocation, critical, demand, surplus, wastage)
    
    if rf is None:
        return None  # CRITICAL FAILURE - episode terminates
    
    # Calculate revenue
    revenue = allocation * rf * productivity
    
    return revenue, rf, critical, demand, surplus, wastage
```

---

## PART C: Persistent Productivity System

### State Variable Definition

```
Productivity_t = clamp(Productivity_{t-1} + ΔProductivity, 0.5, 2.0)
```

Where:
- `Productivity_0 = 1.0` (initial value at episode start)
- `Min_Productivity = 0.5` (lower cap)
- `Max_Productivity = 2.0` (upper cap)

### Delta Productivity Calculation

```
ΔProductivity = 0.05 × (Avg_Revenue_Factor - 1.0)
```

Where:
- `Avg_Revenue_Factor = mean(Revenue_Factor_d for all departments)`
- If avg > 1.0 (profitable): productivity increases
- If avg < 1.0 (loss): productivity decreases
- If avg = 1.0 (break-even): no change

### Productivity Update Algorithm (Python)

```python
def update_productivity(previous_productivity, revenue_factors):
    """
    Update productivity based on average revenue factor.
    
    Args:
        previous_productivity: Productivity from previous round
        revenue_factors: List of revenue factors for all departments
    
    Returns:
        float: New productivity value, clamped to [0.5, 2.0]
    """
    avg_rf = sum(revenue_factors) / len(revenue_factors)
    delta = 0.05 * (avg_rf - 1.0)
    new_productivity = previous_productivity + delta
    
    # Clamp to bounds
    return max(0.5, min(2.0, new_productivity))
```

### Productivity Bounded Behavior

| Avg Revenue Factor | Delta | Productivity Change | Interpretation |
|--------------------|-------|---------------------|----------------|
| 1.8 (peak profit) | +0.04 | Increases toward max | Sectors highly profitable → national growth |
| 1.5 | +0.025 | Moderate increase | Sectors moderately profitable |
| 1.0 | 0 | No change | Break-even state |
| 0.5 | -0.025 | Moderate decrease | Sectors at loss |
| 0.0 (critical) | -0.05 | Large decrease toward min | Sectors failing → national decline |

### Why This Design

1. **Persistence**: Productivity carries over round-to-round, creating long-term consequences
2. **Bounds**: Caps prevent runaway growth (2.0) or collapse (0.5)
3. **Incentive alignment**: Rewards sectors that maintain balanced funding (avg rf ≈ 1.0)
4. **Multiplicative**: Small changes compound over time (50 rounds × 0.05 factor)

---

## PART D: Population Dynamics

### Core Formula

```
Population_t = Population_{t-1} × (1 + Birth_Rate - Death_Rate)
```

### Birth Rate

```
Birth_Rate = Base_Birth_Rate × Productivity_t
```

Where:
- `Base_Birth_Rate = 0.005` (0.5% baseline per round)
- Higher productivity → higher birth rate → faster population growth

### Death Rate

```
Death_Rate = Base_Death_Rate + Crisis_Penalty
```

Where:
- `Base_Death_Rate = 0.002` (0.2% baseline per round)
- `Crisis_Penalty = 0.01` if critical event occurred in round t, else `0`

### Population Update Algorithm (Python)

```python
def update_population(previous_population, productivity, crisis_occurred):
    """
    Update population based on productivity and crisis.
    
    Args:
        previous_population: Population from previous round
        productivity: Current productivity factor
        crisis_occurred: Boolean, True if critical event occurred
    
    Returns:
        int: New population (rounded to nearest whole person)
    """
    base_birth = 0.005
    base_death = 0.002
    crisis_penalty = 0.01 if crisis_occurred else 0.0
    
    birth_rate = base_birth * productivity
    death_rate = base_death + crisis_penalty
    
    new_population = previous_population * (1 + birth_rate - death_rate)
    
    return round(new_population)
```

### Initial Conditions

- `Population_0 = 1,000,000` (one million)

---

## PART E: Time Mapping

### Round to Time Conversion

- **1 round = 3 months (1 quarter)**
- **50 rounds = 12.5 years** (full episode length)

### Display Format for Agents

```
Round t → "Year X, Quarter Y"
```

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

## PART F: Treasury Calculation

### Treasury Update Formula

```
Treasury_t = Treasury_{t-1} - sum(Allocation_d) + sum(Department_Revenue_d) + Baseline_Tax
```

Where:
- `Treasury_{t-1}` = treasury at end of previous round
- `sum(Allocation_d)` = total budget allocated to all departments
- `sum(Department_Revenue_d)` = total revenue generated by all departments
- `Baseline_Tax = 100` (fixed baseline tax per round)

### Alternative Form (End of Round)

```
Treasury_{t+1} = Treasury_t - sum(Consumption_d) + sum(Department_Revenue_d) + Baseline_Tax
```

Note: Under Model A, `Consumption_d = min(Need_d, Allocation_d)` but Revenue uses `Allocation_d × Revenue_Factor`.

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

Key difference from current spec: **Revenue applies SAME round (not next round)**.

---

## PART G: Critical Threshold Failure

### Game Over Condition

```
if Allocation_d < Critical_d for ANY department:
    Episode terminates immediately with CRITICAL_FAILURE
    Final prosperity = (Treasury + sum(Revenue)) / Population
```

### Critical Threshold Formula

```
Critical_d = Demand_d × 0.4
```

Where:
- `Demand_d = Baseline_d × (Population_t / Pop₀) × Event_Multiplier`
- If population-scaled demand changes, critical threshold changes proportionally

### Critical Failure Triggers

| Scenario | Allocation | Critical | Result |
|----------|------------|----------|--------|
| Severe underfunding | 30% of need | 40% of demand | GAME OVER |
| Moderate underfunding | 40% of demand | 40% of demand | BREAK-EVEN (exactly at critical) |
| Adequate funding | 50% of demand | 40% of demand | Survives |
| Well funded | 100% of demand | 40% of demand | Thrives |

---

## PART H: Complete Revenue Factor Lookup Table

For quick reference during implementation, precomputed values at key points:

| Allocation (% of Demand) | 0% | 40% | 50% | 100% | 150% | 250% | 300% |
|--------------------------|-----|-----|-----|------|------|------|------|
| Revenue Factor | FAIL | 0 | 0.25 | 1.0 | 1.8 | 1.0 | ~0.66 |

Where:
- 0% = Critical failure (game over)
- 40% = Critical threshold (break-even at 0)
- 50% = Linear segment mid-point
- 100% = Demand (revenue factor = 1.0)
- 150% = Surplus (revenue factor = 1.8, peak)
- 250% = Wastage (revenue factor = 1.0, returns to break-even)
- 300% = Beyond wastage (exponential decay below 1.0)

---

## Implementation Checklist

- [ ] `revenue_factor(x, critical, demand, surplus, wastage)` returns correct values at all 4 points
- [ ] `Department_Revenue_d = Allocation_d × Revenue_Factor_d × Productivity_t` (uses ALLOCATION, not consumption)
- [ ] Critical threshold causes immediate episode termination
- [ ] Productivity persists across rounds with bounds [0.5, 2.0]
- [ ] Productivity delta = 0.05 × (avg_rf - 1.0)
- [ ] Population initial = 1,000,000
- [ ] Birth rate = 0.005 × Productivity
- [ ] Death rate = 0.002 + crisis penalty
- [ ] Revenue applies same round as allocation
- [ ] Round = 3 months (quarter)
- [ ] 50 rounds = 12.5 years

---

## File Output Location

This specification will be saved to:
```
.sisyphus/plans/wave-1-mathematical-specification.md
```

Wave 2 agents will read this file and implement the formulas exactly when rewriting 04_ECONOMY_MODEL.md and other documents.

---

**End of Wave 1 Mathematical Specification**