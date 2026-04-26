# 10 SUCCESS CRITERIA

> Defines winning and losing conditions, episode boundaries, success metrics, and baseline comparisons for evaluating RL agent performance.

---

## Episode Termination Conditions

### Bankruptcy (Failure)

The episode ends in failure when the treasury is insolvent relative to game rules.

- **Phase 5 (immediate path)**: If `Treasury < sum(Critical_d)` at the start of budget execution, the episode ends with **BANKRUPTCY** (cannot pay mandatory auto-critical)
- **General path**: Treasury at or below zero after debits / standard checks (see Termination Check Phase)
- **Check Timing**: Phase 5 for mandatory-funding bankruptcy; Phase 9 (and other guards) for zero-balance bankruptcy

When bankruptcy occurs:
- All agents receive a bankruptcy penalty of -1000 in that step's reward (reference implementation)
- All subsequent steps receive 0 reward
- Episode total is capped below potential maximum

### Shutdown (Governance Collapse)

The episode ends with status SHUTDOWN when **total approved discretionary** is zero for 2 consecutive rounds.

- **Trigger**: `sum(Discretionary_d) = 0` for 2 consecutive rounds (Option A)
- **Check Timing**: Phase 9 (Termination Check)

When shutdown occurs:
- No bankruptcy penalty (-1000) is applied
- All agents receive 0 for all subsequent steps
- Episode total is sum of rewards up to shutdown
- Shutdown does NOT count as bankruptcy for metrics
- Episodes terminated by Shutdown show "Governance Collapse" rather than "Bankruptcy"

### Max Rounds Reached (Neutral)

- Episode ends after round 50 (12.5 years; 1 round = 3 months)
- No additional reward penalty
- Final state is evaluated against success criteria

### Prosperity Threshold Achieved (Success)

- Episode ends in success if per-capita income (prosperity) meets threshold for 5 consecutive rounds
- **Prosperity Formula**: `(Treasury_t + sum(Department_Revenues_t)) / Population_t`
- **Threshold**: Configurable (default target based on sustainable growth)

---

## Success Metrics

### Primary Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Survival Time** | Number of rounds completed before termination | Maximize (higher is better) |
| **Final Prosperity** | Per-capita income at episode end: `(Treasury + sum(Revenues)) / Population` | Maximize |
| **Population Growth** | `Population_final / Population_initial` | Higher indicates healthy society |
| **Productivity Level** | Final productivity value (0.5-2.0 scale) | Higher indicates productive economy |
| **Crisis Survival** | Number of critical/black swan events successfully navigated | Higher indicates crisis management |
| **Average Revenue Factor** | Mean revenue factor across all departments and rounds | Above 1.0 indicates profitable operation |

### Secondary Metrics

| Metric | Definition | Interpretation |
|--------|------------|----------------|
| **Treasury Return Ratio** | Average treasury surplus (unspent returned to treasury) per round | Higher indicates better system-wide budgeting |
| **Productivity Growth** | Change in productivity from start to end of episode | Positive indicates improving efficiency |
| **Revenue Generation Rate** | Average department revenue per round | Higher indicates productive economy |
| **Treasury Stability** | Variance in treasury balance across rounds | Lower variance indicates stable management |
| **Population Stability** | Variance in population across rounds | Lower variance indicates sustainable growth |

### Scoring Rubric for Hackathon Judging

| Performance Tier | Criteria | Reward Potential |
|------------------|----------|------------------|
| **Exceptional** | Reaches prosperity threshold by round 35 OR survives 50 rounds with final prosperity > 4000 | Full marks |
| **Strong** | Survives 40+ rounds with final prosperity > 2500 | 80% of marks |
| **Competent** | Survives 30+ rounds with final prosperity > 1500 | 60% of marks |
| **Developing** | Survives 20+ rounds with final prosperity > 800 | 40% of marks |
| **Failed** | Bankruptcy or shutdown before round 15 | No marks |

---

## Episode Boundaries

### Start State

- **Round**: 1 (Year 1, Quarter 1)
- **Treasury**: 1000 units
- **Population**: 1,000,000
- **Productivity**: 1.0
- **Departments**: 6 (Social/Municipal, Agriculture, Health, Education/R&D, Defense, Commerce)
- **Treasury Surplus**: 0 (central treasury accumulates unspent allocations)
- **Department Baselines**: Social=60, Agriculture=70, Health=90, Education=80, Defense=100, Commerce=75

### End State

Episode concludes when any termination condition is met:
1. **Bankruptcy**: Treasury cannot pay mandatory critical at Phase 5, or treasury <= 0 per termination checks
2. **Shutdown**: Zero **total discretionary** for 2 consecutive rounds
3. **Max Rounds**: Episode reaches round 50 (12.5 years)
4. **Prosperity Threshold**: Per-capita income meets threshold for 5 consecutive rounds

### State Transitions

```
Round 1 (Start)
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

- **Behavior**: Random budget proposals across the full allocation range
- **Expected Survival**: 5-10 rounds
- **Characterization**: High probability of bankruptcy or shutdown due to uncoordinated random discretionary requests
- **Why It Fails**: No learning; random policy misallocates discretionary spend and bleeds treasury on auto-critical (RF=0 at critical) until bankruptcy or zero-discretionary shutdown

### Greedy Agent Baseline

- **Behavior**: Always requests maximum possible budget for own department, votes yes on all proposals
- **Expected Survival**: 3-5 rounds
- **Characterization**: Rapidly depletes treasury through over-allocation to wastage zone
- **Why It Fails**: Hyperbolic spending pushes allocations far beyond wastage zone (250%+ of demand), where revenue factor drops below 1.0 (break-even). Treasury depletes rapidly from poor ROI.

### Conservative Agent Baseline

- **Behavior**: Always requests exactly demand (100% of baseline) for all departments
- **Expected Survival**: 20-30 rounds
- **Characterization**: Stable but misses profit opportunities
- **Why It Fails**: At exactly demand (100%), revenue factor is 1.0 (break-even). No profit margin. Treasury grows slowly, vulnerable to crises and event costs.

### Optimal Agent Baseline

- **Behavior**: Requests approximately 1.3× demand (in the profit zone between demand and surplus)
- **Expected Survival**: 40+ rounds
- **Characterization**: Achieves revenue factor of ~1.4 by staying in the profit zone
- **Why It Succeeds**: The "sweet spot" of ~130% of demand generates revenue factor of ~1.4, creating positive treasury growth while avoiding wastage zone penalties

### Revenue Factor Reference

| Allocation (% of Demand) | Revenue Factor | Zone |
|--------------------------|----------------|------|
| 0-39% | N/A | Sub-critical RF undefined; Option A funds at least critical when solvent |
| 40% | 0.0 | At critical (zero revenue) |
| 60% | 0.5 | Underfunded |
| 80% | 0.75 | Underfunded |
| 100% | 1.0 | Break-even (demand) |
| 130% | ~1.4 | Profit zone |
| 150% | 1.8 | Peak profit (surplus) |
| 200% | 1.4 | Diminishing returns |
| 250% | 1.0 | Break-even (wastage) |
| 300%+ | < 1.0 | Loss zone |

### Target RL Agent Performance

- **Minimum Acceptable**: Outperforms conservative baseline (survives 25+ rounds, final prosperity > 1500)
- **Target Performance**: Outperforms all baselines significantly (survives 40+ rounds, final prosperity > 2500)
- **Exceptional Performance**: Reaches prosperity threshold by round 35 OR survives 50 rounds with final prosperity > 4000

---

## Metric Collection Protocol

### Per-Round Metrics

At the end of each round (Phase 9), record:
- Current treasury balance
- Current population
- Current productivity level
- Per-department allocation
- Per-department revenue factor
- Per-department revenue generated
- Running reward total

### Episode-End Metrics

When episode terminates, calculate:
- Total rounds survived
- Final prosperity score
- Episode total reward (sum of all step rewards)
- Average revenue factor across all departments and rounds
- Productivity growth (final - initial)
- Population growth ratio (final / initial)
- Treasury stability (variance)

### Baseline Comparison Data

For each trained agent evaluation, record:
- Rounds survived vs. baselines (random: 5-10, greedy: 3-5, conservative: 20-30, optimal: 40+)
- Final prosperity vs. baselines
- Revenue factor performance vs. optimal zone (~1.4)

---

## Design Rationale

- **Mandatory critical with zero RF**: Auto-critical guarantees survival funding when solvent but generates no revenue, so episodes hinge on coordinated **discretionary** investment and treasury health (bankruptcy) rather than a separate “critical failure” termination.
- **Prosperity threshold for success**: Provides a concrete winning condition that requires sustained performance, not just survival. Five consecutive rounds above threshold demonstrates stable governance.
- **Four baseline comparisons**: Give clear benchmarks at different strategy complexity levels. The optimal baseline (~1.3× demand) demonstrates the profit zone insight.
- **Revenue factor as key metric**: Since revenue factor directly determines treasury growth, tracking average revenue factor across episodes provides clear signal of agent performance.
- **Population growth as indicator**: Tracks long-term societal health beyond immediate treasury metrics.
- **Productivity persistence**: Rewards consistent good management through the productivity system's path dependence.
- **Hackathon scoring rubric**: Enables quick judge evaluation without deep game mechanics knowledge.
