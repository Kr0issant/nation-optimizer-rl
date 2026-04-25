# 09 — Reward Model

> Defines the exact reward function for reinforcement learning, measuring "prosperity" as GDP per capita equivalent.

---

## Reward Scope

- **Collective reward only**: ALL agents receive identical reward at each step
- No individual component reward
- Rationale: Incentivizes cooperation over self-interest; mirrors communist principle of collective advancement

---

## Prosperity Definition

Prosperity is defined as the economic output per citizen, analogous to GDP per capita.

### Primary Formula (Recommended)

```
Prosperity_t = (Total_Revenue_t + Treasury_Balance_t) / Population_t
```

Where:
- `Total_Revenue_t` = sum of all department revenues in round t (from Economy Model)
- `Treasury_Balance_t` = treasury balance at end of round t
- `Population_t` = total population at round t (grows with growth rate)
- Population starts at 1000 and grows at 0.5% per round (plus health bonus, minus crisis penalty)

---

## Reward Function

### Per-Step Reward

```
R_t = Base_Reward_t + Productivity_Bonus_t + Efficiency_Bonus_t + Survival_Bonus_t + Allocation_Penalty_t - Bankruptcy_Penalty_t
```

### Component Definitions

#### Base Reward

- `Base_Reward_t = Prosperity_t`
- Measures current prosperity level
- Higher prosperity = higher reward

#### Productivity Bonus

- `Productivity_Bonus_t = +10 * Investment_t`
- Rewards the collective system for actual spending (consumption), not savings
- Investment = sum(Consumption_d) = total actual spending across all departments
- Each unit of investment adds 10 to reward
- Rationale: Productivity rewards actual investment (consumption), not savings

#### Efficiency Bonus

- `Efficiency_Bonus_t = +5 * Count(d where Efficiency_d_t >= 0.9)`
- Rewards departments operating efficiently (Allocation close to Need)
- Efficiency: `Efficiency_d = 1.0 - (|Allocation_d - Need_d| / Need_d)`
- Perfect efficiency = 1.0 when `Allocation = Need`
- Threshold: efficiency >= 0.9 (allocation within 10% of Need)
- Each efficient department adds 5 to reward

#### Survival Bonus

- `Survival_Bonus_t = +1 * Rounds_Survived_t`
- Encourages longevity and avoids bankruptcy
- Each round survived adds 1 to reward (accumulates over episode)

#### Over-Allocation Penalty

- `Over_Allocation_Penalty_t = -5 * Count(d where Allocation_d_t > Need_d_t)`
- Penalty for departments that over-allocated relative to their Need
- Rationale: Over-allocation wastes resources that could be used elsewhere
- Each over-allocated department subtracts 5 from reward

#### Under-Allocation Penalty

- `Under_Allocation_Penalty_t = -10 * Count(d where Allocation_d_t < Need_d_t)`
- Penalty for departments that under-allocated relative to their Need
- Rationale: Under-funding causes departments to underperform
- Each under-allocated department subtracts 10 from reward

#### Bankruptcy Penalty

- `Bankruptcy_Penalty_t = -1000` if `Treasury_t <= 0` else `0`
- Large penalty applied when bankruptcy conditions are met
- Triggers episode termination; all subsequent rewards are 0

#### Shutdown Penalty

- `Shutdown_Penalty_t = 0` (no negative penalty when Shutdown triggers)
- `Survival_Bonus_t` stops accumulating after Shutdown termination
- `Episode_Total = Sum(R_t for t = 1 to T_shutdown)` (no further rewards after Shutdown)
- Shutdown does NOT apply the -1000 Bankruptcy penalty
- Episode ends immediately upon Shutdown; remaining steps receive 0

**Comparison: Shutdown vs Bankruptcy Reward Handling**

| Aspect | Bankruptcy | Shutdown |
|--------|------------|----------|
| Special Penalty | -1000 | 0 |
| Survival Bonus | Stops immediately | Stops immediately |
| Episode Total | Sum rewards up to t, then 0s | Sum rewards up to T_shutdown |
| Final Status | BANKRUPTCY | SHUTDOWN |

---

## Reward Timing

### Per-Step Calculation

- Reward calculated at end of each round (Phase 9: Termination Check)
- Applied immediately to all agents as identical reward
- Used for RL training signal

### Episode Total

- `Episode_Total = Sum(R_t for t = 1 to T)`
- Sum of all per-step rewards across the episode
- Maximized when episode reaches maximum rounds without bankruptcy

### Bankruptcy Termination

- If bankruptcy occurs at step t:
  - Reward for step t includes bankruptcy penalty
  - Steps t+1 through T receive reward = 0
  - Episode total is capped below potential maximum

---

## Alternative Prosperity Formulas

Since prosperity measurement is non-trivial, here are 3 options with trade-offs:

### Option A: Revenue-Based (Primary Formula Recommended Above)

```
Prosperity_t = (Total_Revenue_t + Treasury_Balance_t) / Population
```

- **Pros**: Direct measure of economic activity; aligns with game mechanics
- **Cons**: Treasury balance can fluctuate based on allocation patterns
- **Best for**: Balanced growth; rewards both productivity and savings

### Option B: Efficiency-Weighted Productivity

```
Prosperity_t = Sum(Department_Revenue_d_t * Efficiency_Rating_d_t) / Population
```

- **Pros**: Rewards efficient departments more than inefficient ones
- **Cons**: Can penalize necessary high-spending departments (Defense during crisis)
- **Best for**: Optimizing resource allocation; aggressive efficiency focus

### Option C: Surplus-Driven Growth

```
Prosperity_t = (Baseline_Tax + Sum(Surplus_d_t)) / Population
```

Where:
- `Baseline_Tax` = 100 (constant)
- `Sum(Surplus_d_t)` = total system-wide surplus

- **Pros**: Rewards collective under-spending; encourages frugality
- **Cons**: May discourage necessary investment in infrastructure
- **Best for**: Conservative play; prioritizes savings over investment

### Recommendation for Hackathon

**Use Option A (Primary Formula)** for the following reasons:
1. Intuitive interpretation: Total economic output divided by population
2. Balanced incentives: Rewards both productivity (revenue) and savings (treasury)
3. Stable signal: Less volatile than pure surplus measure
4. Aligns with RL objectives: Clear gradient toward better states

---

## Numerical Examples

### Example 1: Normal Growth Round (Model A)

**Setup:**
- 6 departments: Social (Need=60), Agriculture (Need=70), Health (Need=90), Education (Need=80), Defense (Need=100), Commerce (Need=75)
- Population = 1000
- Round 1: All allocations match Need exactly
- Social=60, Agriculture=70, Health=90, Education=80, Defense=100, Commerce=75
- Treasury balance after allocations = 1525 (1000 initial - 475 allocated)

**Model A Calculation:**
- All departments: Allocation = Need, so Consumption = Need
- Social: Efficiency = 1.0, Investment contribution = 60
- Agriculture: Efficiency = 1.0, Investment contribution = 70
- Health: Efficiency = 1.0, Investment contribution = 90
- Education: Efficiency = 1.0, Investment contribution = 80
- Defense: Efficiency = 1.0, Investment contribution = 100
- Commerce: Efficiency = 1.0, Investment contribution = 75

Total Investment = 475 (sum of all consumption)
Total Need = 475

Productivity_Multiplier = 1.0 + (475/475) = 2.0

Department Revenues:
- All: Revenue = Consumption * Efficiency * Productivity_Multiplier = Need * 1.0 * 2.0 = 2 * Need
- Social: 60 * 2 = 120
- Agriculture: 70 * 2 = 140
- Health: 90 * 2 = 180
- Education: 80 * 2 = 160
- Defense: 100 * 2 = 200
- Commerce: 75 * 2 = 150

Total Revenue = 950

**Reward Calculation:**

```
Total_Revenue = 950
Treasury_Balance = 1525
Population = 1000
Prosperity = (950 + 1525) / 1000 = 2.475

Base_Reward = 2.475
Productivity_Bonus = +10 * 475 = +4750 (investment-driven)
Efficiency_Bonus = +5 * 6 = +30 (all departments at 1.0 efficiency)
Survival_Bonus = +1 * 1 = +1
Over_Allocation_Penalty = 0 (no over-allocation)
Under_Allocation_Penalty = 0 (no under-allocation)
Bankruptcy_Penalty = 0 (treasury > 0)

R_t = 2.475 + 4750 + 30 + 1 - 0 - 0 = 4783.475
```

**Result:** Reward = 4783.475 for all agents in this step

Note: The productivity bonus heavily rewards investment (actual consumption). Perfect efficiency across all departments yields maximum efficiency bonus.

---

### Example 2: Crisis Management Round (Model A)

**Setup:**
- 6 departments with baseline needs
- Population = 1012 (after 2 rounds of growth)
- War event increases Defense Need from 100 to 250
- Round 3 allocations: Health=90, Education=80, Defense=200, Social=60, Agriculture=70, Commerce=75
- Treasury balance = 800 (depleted from crisis spending)
- Rounds survived = 3

**Model A Calculation:**
- Health: Need=90, Allocation=90, Consumption=90, Efficiency=1.0
- Education: Need=80, Allocation=80, Consumption=80, Efficiency=1.0
- Defense: Need=250 (war), Allocation=200, Consumption=200, Efficiency=1.0-(50/250)=0.8
- Social: Need=60, Allocation=60, Consumption=60, Efficiency=1.0
- Agriculture: Need=70, Allocation=70, Consumption=70, Efficiency=1.0
- Commerce: Need=75, Allocation=75, Consumption=75, Efficiency=1.0

Total Investment = 90 + 80 + 200 + 60 + 70 + 75 = 575
Total Need = 90 + 80 + 250 + 60 + 70 + 75 = 625

Productivity_Multiplier = 1.0 + (575/625) = 1.92

Department Revenues:
- Health: 90 * 1.0 * 1.92 = 172.8
- Education: 80 * 1.0 * 1.92 = 153.6
- Defense: 200 * 0.8 * 1.92 = 307.2
- Social: 60 * 1.0 * 1.92 = 115.2
- Agriculture: 70 * 1.0 * 1.92 = 134.4
- Commerce: 75 * 1.0 * 1.92 = 144.0

Total Revenue = 1027.2

**Reward Calculation:**

```
Total_Revenue = 1027.2
Treasury_Balance = 800
Population = 1012
Prosperity = (1027.2 + 800) / 1012 = 1.806

Base_Reward = 1.806
Productivity_Bonus = +10 * 575 = +5750 (high investment during crisis)
Efficiency_Bonus = +5 * 5 = +25 (5 of 6 departments >= 0.9 efficiency)
Survival_Bonus = +1 * 3 = +3
Over_Allocation_Penalty = 0
Under_Allocation_Penalty = -10 * 1 (Defense: 200 < 250) = -10
Bankruptcy_Penalty = 0

R_t = 1.806 + 5750 + 25 + 3 - 10 - 0 = 5769.806
```

**Result:** Reward = 5769.806 for all agents in this step. Note Defense is underfunded due to crisis, incurring under-allocation penalty.

---

### Example 3: Bankruptcy Scenario (Model A)

**Setup:**
- Treasury balance drops to 0 during Phase 5
- Total Allocation = 600, Treasury before allocation = 400
- Bankruptcy triggered: sum(Allocation) > Treasury

**Reward Calculation:**

```
Prosperity = (revenue generated before bankruptcy + treasury) / population
Suppose: Total_Revenue = 200, Treasury_Balance = 0, Population = 1000
Prosperity = (200 + 0) / 1000 = 0.2

Base_Reward = 0.2
Productivity_Bonus = +10 * Investment (say 400) = +4000
Efficiency_Bonus = +5 * 2 = +10
Survival_Bonus = +1 * 2 = +2
Under_Allocation_Penalty = -10 * 3 = -30
Bankruptcy_Penalty = -1000

R_t = 0.2 + 4000 + 10 + 2 - 30 - 1000 = 2982.2
```

**Result:** Despite negative bankruptcy penalty, reward is positive because productivity bonus (investment-driven) and survival bonus accumulated before bankruptcy. Episode terminated; remaining steps receive 0.

---

## Summary of Reward Components

| Component | Formula | Range |
|-----------|---------|-------|
| Base Reward | `Prosperity_t` | (-inf, +inf) |
| Productivity Bonus | `+10 * Investment_t` | [0, +inf) |
| Efficiency Bonus | `+5 * Count(Efficiency_d_t >= 0.9)` | [0, +inf) |
| Survival Bonus | `+1 * Rounds_Survived_t` | [0, +inf) |
| Over-Allocation Penalty | `-5 * Count(Allocation_d_t > Need_d_t)` | (-inf, 0] |
| Under-Allocation Penalty | `-10 * Count(Allocation_d_t < Need_d_t)` | (-inf, 0] |
| Bankruptcy Penalty | `-1000 if bankrupt else 0` | {-1000, 0} |

Where `Efficiency_d_t = 1.0 - (|Allocation_d_t - Need_d_t| / Need_d_t)` and `Investment_t = sum(Consumption_{d,t})`

---

## Design Rationale

- **Collective reward** aligns with parliamentary cooperation requirement
- **Prosperity as GDP per capita** provides intuitive, economically grounded signal
- **Model A (Government Budget Execution)**: Treasury only pays for actual consumption
- **Productivity bonus** incentivizes unspent allocation returning to treasury (treasury return)
- **Efficiency bonus** rewards accurate budgeting: agents want `Allocation ≈ Need`
- **Over-allocation penalty** discourages wasteful spending (Allocation > Need)
- **Under-allocation penalty** discourages under-funding critical departments
- **Survival bonus** discourages reckless behavior that triggers bankruptcy
- **Bankruptcy penalty** creates strong incentive to avoid treasury depletion
- **No individual component** prevents zero-sum competition between ministers