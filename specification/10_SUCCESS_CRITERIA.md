# 10 SUCCESS CRITERIA

> Defines winning and losing conditions, episode boundaries, success metrics, and baseline comparisons for evaluating RL agent performance.

---

## Episode Termination Conditions

### Bankruptcy (Failure)

The episode ends immediately in failure when ANY of the following occur:

- **Treasury Bankruptcy**: Treasury drops to 0 or below during Phase 5 (Budget Execution) or Phase 9 (Termination Check)
- **Department Over-Consumption**: Any department's deficit exceeds 0 at the end of Phase 6 (Consumption and Event Impact)

When bankruptcy occurs:
- All agents receive a bankruptcy penalty of -1000 in that step's reward
- All subsequent steps receive 0 reward
- Episode total is capped below the potential maximum

### Shutdown (Governance Collapse)

The episode ends with status SHUTDOWN when `sum(Allocation_d) = 0` for 2 consecutive rounds.

When shutdown occurs:
- No bankruptcy penalty (-1000) is applied
- All agents receive 0 for all subsequent steps
- Episode total is sum of rewards up to shutdown
- Shutdown does NOT count as bankruptcy for metrics
- Episodes terminated by Shutdown show "Failed State" rather than "Bankruptcy"

### Max Rounds Reached (Neutral)

- Episode ends after round 50 (configurable via `max_rounds` parameter)
- No additional reward penalty
- Final state is evaluated against success criteria

### Prosperity Threshold Achieved (Success)

- Episode ends in success if prosperity reaches 5000 or higher for 3 consecutive rounds
- Prosperity formula: `(Total_Revenue_t + Treasury_Balance_t) / Population`
- Provides a strong positive signal that the system is thriving

---

## Success Metrics

### Primary Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Survival Time** | Number of rounds completed before termination | Maximize (higher is better) |
| **Final Prosperity** | Prosperity value at episode end: `(Total_Revenue + Treasury) / Population` | Maximize |
| **Episode Total Reward** | Sum of all per-step rewards across episode | Maximize |
| **Population Growth** | Cumulative population growth over episode | Higher indicates healthy society |
| **Crisis Survival Rate** | Percentage of critical (severity 5) events successfully navigated | Higher indicates crisis management |

### Secondary Metrics

| Metric | Definition | Interpretation |
|--------|------------|----------------|
| **Treasury Return Ratio** | Average treasury surplus (unspent returned to treasury) per round | Higher indicates better system-wide budgeting |
| **Efficiency Score** | Mean efficiency rating across all departments | Above 1.0 indicates efficient operation |
| **Revenue Generation Rate** | Average department revenue per round | Higher indicates productive economy |
| **Treasury Stability** | Variance in treasury balance across rounds | Lower variance indicates stable management |
| **Investment Rate** | Average investment (consumption) per round | Higher indicates productive economy |

### Scoring Rubric for Hackathon Judging

| Performance Tier | Criteria | Reward Potential |
|------------------|----------|------------------|
| **Exceptional** | Reaches prosperity 5000+ by round 30 OR survives 50 rounds with final prosperity > 3000 | Full marks |
| **Strong** | Survives 40+ rounds with final prosperity > 2000 | 80% of marks |
| **Competent** | Survives 25+ rounds with final prosperity > 1000 | 60% of marks |
| **Developing** | Survives 15+ rounds with final prosperity > 500 | 40% of marks |
| **Failed** | Bankruptcy before round 15 | No marks |

**Note:** Due to the new event distribution (40% no events, 35% minor/positive, 20% moderate/major, 4% critical, 1% compound crisis), baseline survival expectations have changed. Most rounds are normal government operations with no disruption. Black swan crises (Financial Collapse, Natural Disaster, Pandemic) are rare but devastating.

---

## Episode Boundaries

### Start State

- **Round**: 0
- **Treasury**: 1000 units
- **Population**: 1 (default)
- **Departments**: Even number initialized (4, 6, 8, etc.)
- **Treasury Surplus**: 0 (central treasury accumulates unspent allocations)
- **Department Efficiency Rating**: 1.0 for all departments
- **Rounds Survived Counter**: 0

### End State

Episode concludes when any termination condition is met:
1. Bankruptcy triggered (treasury <= 0 OR department deficit > 0)
2. Shutdown triggered (zero allocation for 2 consecutive rounds)
3. Max rounds reached (round >= 50)
4. Prosperity threshold achieved (prosperity >= 5000 for 3 consecutive rounds)

### State Transitions

```
Round 0 (Start)
    ↓
Phase 1-9 Execution
    ↓
Termination Check (Phase 9)
    ↓
[Continue] → Next Round
[Terminate] → Record Final State → Calculate Episode Total
```

---

## Baseline Comparisons

### Random Agent Baseline

- **Behavior**: Random budget proposals (0 to max treasury), random votes (yes/no/abstain)
- **Expected Survival**: 15-25 rounds (due to 40% no-event rounds)
- **Expected Final Prosperity**: 300-600
- **Characterization**: Fails due to uncoordinated allocations and occasional treasury depletion
- **Why It Fails**: No learning; random proposals lead to either over-allocation (bankruptcy) or under-allocation (department deficits)

### Greedy Agent Baseline

- **Behavior**: Always requests maximum possible budget for own department, votes yes on all proposals
- **Expected Survival**: 8-15 rounds
- **Expected Final Prosperity**: 150-350
- **Characterization**: Rapidly depletes treasury through excessive allocations
- **Why It Fails**: Hyperbolic spending depletes treasury before generating sustainable revenue

### Cooperative Baseline (Equal Division)

- **Behavior**: Divides treasury equally among all departments each round, votes fairly on all proposals
- **Expected Survival**: 30-45 rounds
- **Expected Final Prosperity**: 1500-3000
- **Characterization**: Stable and benefits from the new mostly-normal event distribution
- **Why It Fails**: Equal division ignores individual department needs and efficiency potential

### Target RL Agent Performance

- **Minimum Acceptable**: Outperforms cooperative baseline (survives 35+ rounds, final prosperity > 2000)
- **Target Performance**: Outperforms all baselines significantly (survives 45+ rounds, final prosperity > 3000)
- **Exceptional Performance**: Reaches prosperity threshold (5000) within 35 rounds OR survives 50 rounds with final prosperity > 4000

---

## Metric Collection Protocol

### Per-Round Metrics

At the end of each round (Phase 9), record:
- Current treasury balance
- Current prosperity value
- Per-department efficiency ratings
- Per-department surplus/deficit
- Running reward total

### Episode-End Metrics

When episode terminates, calculate:
- Total rounds survived
- Final prosperity score
- Episode total reward (sum of all step rewards)
- Average budget balance ratio across all rounds
- Average efficiency score across all rounds
- Treasury stability (variance)

### Baseline Comparison Data

For each trained agent evaluation, record:
- Rounds survived vs. random agent (expected 10-15)
- Final prosperity vs. greedy agent (expected 100-200)
- Episode reward vs. cooperative baseline (expected 800-1500 episode total)

---

## Design Rationale

- **Survival time as primary metric**: Incentivizes agents to avoid risky behavior that leads to early bankruptcy
- **Prosperity threshold for success**: Provides a concrete winning condition that requires sustained performance, not just survival
- **Three baseline comparisons**: Give clear benchmarks at different strategy complexity levels
- **Hackathon scoring rubric**: Enables quick judge evaluation without deep game mechanics knowledge
- **Budget balance and efficiency metrics**: Encourage agents to optimize rather than just survive
- **Bankruptcy as immediate termination**: Creates strong stakes for every allocation decision
