# 09 — Reward Model

> Defines the exact reward function for reinforcement learning, measuring "prosperity" as per-capita income with piecewise revenue incentives.

---

## Reward Scope

- **Collective reward only**: ALL agents receive identical reward at each step
- No individual component reward
- Rationale: Incentivizes cooperation over self-interest; mirrors collective advancement principle

---

## Prosperity Definition

Prosperity is defined as the economic output per citizen, analogous to GDP per capita.

### Primary Formula (Recommended)

```
Prosperity_t = Total_Revenue_t / Population_t
```

Where:
- `Total_Revenue_t` = sum of all department revenues in round t (from Economy Model piecewise curve)
- `Population_t` = total population at round t
- Population starts at 1,000,000 and grows based on productivity and health

**Key difference from old model**: Dividing by population (not treasury) gives per-capita income. The piecewise revenue curve means agents can optimize for profit zone allocations rather than exact demand matching.

---

## Reward Function

### Per-Step Reward

```
R_t = Base_Reward_t + Productivity_Bonus_t + Survival_Bonus_t + Allocation_Penalty_t + Bankruptcy_Adjustment_t
```

Under Option A there is **no** `-1000` “critical failure” penalty component: mandatory critical funding prevents that termination class. **Bankruptcy** may still apply a large negative adjustment via the same bookkeeping field in code (`critical_penalty` slot used for `BANKRUPTCY_PENALTY` in the reference implementation).

### Component Definitions

#### Base Reward

- `Base_Reward_t = Prosperity_t`
- Measures current prosperity level (revenue per capita)
- Higher revenue per capita = higher reward

#### Productivity Bonus

- `Productivity_Bonus_t = +50 × (Productivity_t - 1.0)`
- Rewards high national productivity
- Productivity is **persistent** across rounds, so this bonus rewards long-term good budgeting decisions
- If Productivity = 1.5: bonus = +25
- If Productivity = 2.0: bonus = +50 (maximum)
- If Productivity = 0.5: bonus = -25 (productivity penalty)
- Rationale: Sustained profitable allocation (avg revenue factor > 1.0) pushes productivity upward, which then amplifies all revenue generation

#### Survival Bonus

- `Survival_Bonus_t = +10 × Rounds_Survived_t`
- Encourages longevity and sustained governance
- Each round survived adds 10 to reward (accumulates over episode)
- At round 10: survival bonus = 100
- At round 50: survival bonus = 500

#### Allocation Penalty

The piecewise curve creates three allocation zones with different penalty structures:

**Over-Allocation Penalty (Wastage Zone)**
- `Over_Allocation_Penalty_t = -5 × Count(sectors where Allocation_d > Surplus_d)`
- Penalty for sectors in the wastage zone (allocation above surplus threshold)
- Each wastage sector subtracts 5 from reward
- Rationale: Over-allocation beyond surplus wastes resources, revenue factor drops below 1.0

**Under-Allocation Penalty (Below Demand but Above Critical)**
- `Under_Allocation_Penalty_t = -10 × Count(sectors where Critical_d ≤ Allocation_d < Demand_d)`
- Penalty for sectors between critical and demand (linear growth zone)
- Each under-funded sector subtracts 10 from reward
- Rationale: Under-funding causes revenue factor below 1.0, reducing national productivity

**No Penalty Zone: Demand to Surplus**
- Sectors with `Demand_d ≤ Allocation_d ≤ Surplus_d` receive NO penalty
- This is the profit zone where revenue factor ranges from 1.0 to 1.8
- Agents WANT to allocate in this zone, not exactly at demand

#### Bankruptcy adjustment (termination)

- When the episode ends in **BANKRUPTCY**, the reference implementation applies a large negative penalty (same magnitude historically used for hard failures) so terminal states remain clearly worse than healthy survival
- There is **no** parallel penalty for “critical failure” as a termination reason — that condition was removed under Option A

---

## Reward Timing

### Per-Step Calculation

- Reward calculated at end of each round after revenue generation
- Applied immediately to all agents as identical reward
- Used for RL training signal

### Episode Total

- `Episode_Total = Sum(R_t for t = 1 to T)`
- Sum of all per-step rewards across the episode
- Maximized when episode reaches maximum rounds without bankruptcy / shutdown

### Bankruptcy termination

- If bankruptcy occurs at step t:
  - Reward for step t includes the configured bankruptcy penalty (reference: -1000 via penalty slot)
  - Episode terminates immediately
  - Steps t+1 through T receive 0

---

## Alternative Prosperity Formulas

Since prosperity measurement has trade-offs, here are 3 options:

### Option A: Revenue-Based (Primary Formula Recommended Above)

```
Prosperity_t = Total_Revenue_t / Population_t
```

- **Pros**: Direct per-capita output; clear signal of economic productivity
- **Cons**: Does not account for treasury reserves
- **Best for**: Optimizing revenue generation; rewards efficient allocation

### Option B: Efficiency-Weighted Prosperity

```
Prosperity_t = Sum(Revenue_d_t × Revenue_Factor_d_t) / Population_t
```

- **Pros**: Rewards departments that generate revenue efficiently (high revenue factor)
- **Cons**: Can undervalue necessary high-spending during crises
- **Best for**: Allocation optimization; rewards profit zone behavior

### Option C: Treasury-Weighted Prosperity

```
Prosperity_t = (Total_Revenue_t + Treasury_Balance_t) / Population_t
```

- **Pros**: Includes accumulated reserves; rewards saving
- **Cons**: May discourage necessary spending during crises
- **Best for**: Conservative play; balances revenue and savings

### Recommendation

**Use Option A (Primary Formula)** for the following reasons:
1. Per-capita signal aligns with population dynamics (larger population = harder to grow prosperity)
2. Clear gradient toward profitable allocation (revenue factor > 1.0)
3. Persistent productivity already handles long-term savings consideration
4. Aligns with RL objectives: prosperity grows when allocation decisions are sound

---

## Piecewise Revenue Zone Reference

Understanding allocation zones is essential for reward optimization:

| Zone | Allocation Range | Revenue Factor | Reward Treatment |
|------|-----------------|----------------|------------------|
| **At / above critical** | `x ≥ Critical_d` | 0 at critical, then 0–1.0 to demand | Under-demand band uses under-allocation penalty when `x < Demand_d` |
| **Under-Funded** | `Critical_d ≤ x < Demand_d` | 0 to 1.0 (linear) | -10 per sector (under-allocation penalty) |
| **Profit Zone** | `Demand_d ≤ x ≤ Surplus_d` | 1.0 to 1.8 (linear) | NO PENALTY (agents want to be here) |
| **Wastage Zone** | `x > Surplus_d` | 1.8 decaying to 1.0+ | -5 per sector (over-allocation penalty) |

**Key insight**: The profit zone (Demand to Surplus) is where agents should aim allocations. This is approximately 1.0× to 1.5× demand, not exactly 1.0× demand.

---

## Numerical Examples

### Example 1: Normal Round with Profit Zone Allocations

**Setup:**
- 6 departments: Social (Baseline=60), Agriculture (Baseline=70), Health (Baseline=90), Education (Baseline=80), Defense (Baseline=100), Commerce (Baseline=75)
- Population = 1,000,000
- Productivity = 1.0
- Round 5: All allocations in profit zone (between demand and surplus)
- No events (event multiplier = 1.0)

**Allocation Strategy (150% of demand):**
- Social: 90, Agriculture: 105, Health: 135, Education: 120, Defense: 150, Commerce: 112.5
- All above demand, below or at surplus

**Threshold Calculation (per department):**
- Demand_d = Baseline × (Population / 1,000,000) × 1.0 = Baseline
- Surplus_d = Demand × 1.5 = 1.5 × Baseline

**Revenue Factor (all at surplus):**
- Revenue Factor = 1.8 for all departments (peak profit zone)

**Department Revenues:**
- Social: 90 × 1.8 × 1.0 = 162
- Agriculture: 105 × 1.8 × 1.0 = 189
- Health: 135 × 1.8 × 1.0 = 243
- Education: 120 × 1.8 × 1.0 = 216
- Defense: 150 × 1.8 × 1.0 = 270
- Commerce: 112.5 × 1.8 × 1.0 = 202.5
- Total Revenue = 1282.5

**Prosperity:**
- Prosperity = 1282.5 / 1,000,000 = 0.0012825

**Reward Calculation:**
```
Base_Reward = 0.0012825 (prosperity)
Productivity_Bonus = +50 × (1.0 - 1.0) = 0 (neutral productivity)
Survival_Bonus = +10 × 5 = +50 (5 rounds survived)
Over_Allocation_Penalty = -5 × 0 = 0 (no sectors in wastage zone)
Under_Allocation_Penalty = -10 × 0 = 0 (no sectors below demand)
Critical_Penalty = 0 (no sector below critical)

R_t = 0.0012825 + 0 + 50 + 0 + 0 - 0 = 50.0012825
```

**Result:** Reward = 50.0012825 for all agents. Note the survival bonus dominates; productivity bonus is zero because productivity has not yet changed.

---

### Example 2: Crisis Round with Under-Funded Sector

**Setup:**
- Population = 1,010,000 (grew slightly)
- Productivity = 1.2 (sustained profit zone increased productivity)
- Round 10: War event increases Defense Need
- Defense allocation below demand but above critical

**Allocations:**
- Social: 60 (at demand), Agriculture: 70 (at demand), Health: 90 (at demand)
- Education: 80 (at demand), Defense: 80 (below demand=100, but above critical=40)
- Commerce: 75 (at demand)

**Threshold Calculation:**
- Defense: Baseline=100, Demand=100, Critical=40, Surplus=150

**Revenue Factors:**
- Social: 1.0 (at demand)
- Agriculture: 1.0 (at demand)
- Health: 1.0 (at demand)
- Education: 1.0 (at demand)
- Defense: (80 - 40) / (100 - 40) = 40/60 = 0.667 (linear segment)
- Commerce: 1.0 (at demand)

**Department Revenues:**
- Social: 60 × 1.0 × 1.2 = 72
- Agriculture: 70 × 1.0 × 1.2 = 84
- Health: 90 × 1.0 × 1.2 = 108
- Education: 80 × 1.0 × 1.2 = 96
- Defense: 80 × 0.667 × 1.2 = 64
- Commerce: 75 × 1.0 × 1.2 = 90
- Total Revenue = 514

**Prosperity:**
- Prosperity = 514 / 1,010,000 = 0.000509

**Reward Calculation:**
```
Base_Reward = 0.000509 (prosperity)
Productivity_Bonus = +50 × (1.2 - 1.0) = +10 (elevated productivity)
Survival_Bonus = +10 × 10 = +100 (10 rounds survived)
Over_Allocation_Penalty = -5 × 0 = 0 (no wastage)
Under_Allocation_Penalty = -10 × 1 (Defense below demand) = -10
Critical_Penalty = 0 (Defense above critical)

R_t = 0.000509 + 10 + 100 - 10 - 0 = 100.000509
```

**Result:** Reward = 100.000509. Defense under-funding costs 10 points, but high productivity and survival bonuses more than compensate.

---

### Example 3: Bankruptcy Round (Game Over)

**Setup:**
- Treasury cannot cover `sum(Critical_d)` at Phase 5 execution (mandatory spend exceeds balance)
- Episode terminates with **BANKRUPTCY**

**Reward at Termination:**
- Reference implementation: large negative bankruptcy adjustment on the terminal step (e.g. -1000 in the penalty slot), plus usual components where applicable
- No separate “critical failure” component

---

## Summary of Reward Components

| Component | Formula | Range |
|-----------|---------|-------|
| Base Reward | `Prosperity_t` | (-inf, +inf) |
| Productivity Bonus | `+50 × (Productivity_t - 1.0)` | (-25, +50) |
| Survival Bonus | `+10 × Rounds_Survived_t` | [0, +inf) |
| Over-Allocation Penalty | `-5 × Count(sectors where Allocation > Surplus)` | (-inf, 0] |
| Under-Allocation Penalty | `-10 × Count(sectors where Critical ≤ Allocation < Demand)` | (-inf, 0] |
| Bankruptcy adjustment | Large negative on terminal bankruptcy step (implementation-defined) | (-inf, 0] |

---

## Design Rationale

### Collective Reward Alignment

- All agents receive identical reward: aligns incentives toward cooperative budgeting
- Individual department performance affects collective reward through revenue generation

### Profit Zone Incentive

- The piecewise curve creates a profit zone between demand and surplus
- Agents are rewarded for allocating moderately above demand (1.0× to 1.5×) rather than exactly at demand
- This differs fundamentally from old linear efficiency penalty where any deviation was penalized

### Persistent Productivity Connection

- Productivity persists across rounds, creating long-term consequence
- Sustained profit zone (avg revenue factor > 1.0) pushes productivity toward 2.0
- High productivity amplifies all revenue generation, creating compounding rewards
- This connects budget decisions to multi-round strategy, not just single-round optimization

### Mandatory critical and discretionary incentives

- Auto-critical guarantees survival funding when solvent, so reward shaping focuses on **discretionary** investment and zone penalties (under / over demand vs. surplus)
- Treasury stress appears as **bankruptcy** when mandatory spend is unaffordable

### Population Dynamics Impact

- Per-capita prosperity means population growth makes prosperity harder to increase
- Birth rate tied to productivity: high productivity = faster population growth
- Population growth increases demand across all sectors, requiring more total allocation
- Balanced approach needed: enough revenue to grow prosperity despite larger population

---

## Comparison: Old vs New Reward Model

| Aspect | Old Model | New Model |
|--------|-----------|-----------|
| Prosperity | `(Revenue + Treasury) / Population` | `Revenue / Population` |
| Base Reward | Prosperity | Prosperity |
| Productivity Bonus | `+10 × Investment` (consumption-based) | `+50 × (Productivity - 1.0)` (persistent) |
| Efficiency Zone | `Allocation ≈ Need` (exact match) | `Demand ≤ Allocation ≤ Surplus` (profit zone) |
| Over-Allocation | `-5 × Count(Allocation > Need)` | `-5 × Count(Allocation > Surplus)` (wastage zone only) |
| Under-Allocation | `-10 × Count(Allocation < Need)` | `-10 × Count(Critical ≤ Allocation < Demand)` |
| Failure Mode | Bankruptcy (treasury ≤ 0 or cannot pay `sum(Critical_d)` at execution) | (Critical failure termination removed under Option A) |
| Penalty Severity | Large negative on terminal step (e.g. -1000) | — |

**Key shift**: The new model rewards profit zone behavior rather than exact demand matching. Agents can target ~1.3× demand for peak revenue factor of 1.8 without penalty.

---

(End of file - total 354 lines)