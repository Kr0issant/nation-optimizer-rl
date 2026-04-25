# F2: Consistency Check Report

**Date**: 2026-04-25
**Task**: F2 - Consistency Check across all specification documents
**Documents Reviewed**: 00_INDEX.md, 01_GAME_OVERVIEW.md, 02_GAME_RULES_REFERENCE.md, 03_TURN_STRUCTURE.md, 04_ECONOMY_MODEL.md, 05_VOTING_PROTOCOL.md, 06_EVENT_SYSTEM.md, 07_AGENT_ACTION_SPACE.md, 08_OBSERVATION_SPACE.md, 09_REWARD_MODEL.md, 10_SUCCESS_CRITERIA.md, 11_GUARDRAILS.md, 12_GLOSSARY.md, APPENDIX_A_EXAMPLES.md

---

## EXECUTIVE SUMMARY

| Check | Status |
|-------|--------|
| Term Coverage | ⚠️ PARTIAL - 20+ terms missing from glossary |
| Treasury Formula | ❌ INCONSISTENT - APPENDIX contradicts 04 |
| Reward Formula | ✅ CONSISTENT |
| Voting Rules | ✅ CONSISTENT |
| Event Visibility | ✅ CONSISTENT |
| Surplus Mechanic | ✅ CONSISTENT (treasury-level) |
| Event Timing | ✅ CONSISTENT |
| Revenue Timing | ✅ CONSISTENT |
| Bankruptcy Threshold | ✅ CONSISTENT |
| Majority Definition | ✅ CONSISTENT |

**Critical Issue Found**: Treasury formula inconsistency between 04_ECONOMY_MODEL.md and APPENDIX_A_EXAMPLES.md

---

## 1. TERM COVERAGE CHECK

### Terms in Glossary (12_GLOSSARY.md)
1. Agent / Minister
2. Bankruptcy
3. Baseline Tax Revenue
4. Budget
5. Central Treasury
6. Department
7. Episode
8. Event
9. Event Ledger
10. Portfolio
11. Productivity
12. Proposal / Budget Proposal
13. Prosperity
14. Revenue
15. Severity
16. Surplus
17. Term / Round
18. Vote

### Capitalized Terms NOT in Glossary

| Term | Found In | Definition Available |
|------|----------|---------------------|
| Treasury-level surplus | 01, 02, 03, 04, APPENDIX | Yes - 04 |
| Department surplus | 02 only | Implied but not defined |
| Abstention | 02, 05 | Yes - 05 defines rules |
| Majority threshold | 02, 05 | Yes - 05 |
| Tie = Rejection | 05 | Yes - 05 |
| Efficiency Rating | 04 | Yes - 04 |
| Efficiency Rating_d | 04 | Yes - 04 |
| Productivity Multiplier | 04 | Yes - 04 |
| Productivity Bonus | 04, 09 | Yes - 04 |
| Productivity Bonus_t | 09 | Yes - 09 |
| Efficiency Bonus_t | 09 | Yes - 09 |
| Survival Bonus_t | 09 | Yes - 09 |
| Over-Allocation Penalty_t | 09 | Yes - 09 |
| Under-Allocation Penalty_t | 09 | Yes - 09 |
| Bankruptcy Penalty_t | 09 | Yes - 09 |
| Treasury Surplus | 04 | Yes - 04 |
| Treasury Surplus_t | 04 | Yes - 04 |
| Department Revenue | 04 | Yes - 04 |
| Department_Revenues | 04 | Yes - 04 |
| Consumption Efficiency | 04 | Yes - 04 |
| Consumption_Efficiency_d | 04 | Yes - 04 |
| Deficit_d | 04 | Yes - 04 |
| Event Cost | 06 | Yes - 06 |
| Base Cost | 06 | Yes - 06 |
| Severity_Multiplier | 06 | Yes - 06 |
| Random_Variance | 06 | Yes - 06 |
| Public Information | 08 | No |
| Private Information | 08 | No |
| Hidden Information | 08 | No |
| Random Agent Baseline | 10 | No |
| Greedy Agent Baseline | 10 | No |
| Cooperative Baseline | 10 | No |
| Max Rounds | 10 | No |
| Prosperity Threshold | 10 | No |
| Guardrails | 11 | No |
| PROPOSE_BUDGET | 07 | Yes - 07 |
| VOTE | 07 | Yes - 07 |
| DEBATE | 07 | Yes - 07 |
| ABSTAIN_FROM_PROPOSAL | 07 | Yes - 07 |

### Missing Terms Summary
**Critical missing definitions** (core game terms used in formulas but not in glossary):
- `Treasury_Surplus` / `Treasury-level surplus` - central to economy
- `Productivity Multiplier` - appears in formula
- `Efficiency Rating` - appears in formula
- `Department Revenue` - appears in formula

**Action terms** - should be in glossary or explicitly cross-referenced:
- `PROPOSE_BUDGET`, `VOTE`, `DEBATE`, `ABSTAIN_FROM_PROPOSAL`

**Baseline terms** - used in success criteria but not defined:
- `Random Agent Baseline`, `Greedy Agent Baseline`, `Cooperative Baseline`

---

## 2. FORMULA CONSISTENCY CHECK

### 2.1 Treasury Formula

**04_ECONOMY_MODEL.md states:**
```
Treasury_t = Baseline_Tax + Productivity_Bonus_{t-1} + Sum(Department_Revenues_{t-1})
```
Where:
- Baseline_Tax = 100 (constant)
- Productivity_Bonus_{t-1} from round t-1
- Sum(Department_Revenues_{t-1}) from round t-1

**APPENDIX_A_EXAMPLES.md shows:**

**Example 1, Round 2 Starting Treasury:**
```
Treasury_2 = Baseline_Tax (100) + Productivity_Bonus (47.6) + Department_Revenues (988.7) + Treasury_Surplus_Rollover (80) = 1216.3
```

**Example 4, Round 2 Starting Treasury:**
```
Treasury_2 = 100 + 45 + 999.8 + 90 = 1234.8
```
Where 90 = Treasury_Surplus from Round 1.

**Example 4, Round 3 Starting Treasury:**
```
Treasury_3 = 100 + 27.5 + 903.9 + 55 = 1086.4
```
Where 55 = Treasury_Surplus from Round 2.

**⚠️ CRITICAL INCONSISTENCY DETECTED:**

The formula in 04_ECONOMY_MODEL.md does NOT include Treasury_Surplus as a direct addend:
```
Treasury_t = Baseline_Tax + Productivity_Bonus_{t-1} + Sum(Department_Revenues_{t-1})
```

But the APPENDIX examples consistently add Treasury_Surplus from the previous round:
```
Treasury_t = Baseline_Tax + Productivity_Bonus_{t-1} + Sum(Department_Revenues_{t-1}) + Treasury_Surplus_{t-1}
```

**04_ECONOMY_MODEL.md Section "Treasury Surplus Rollover" states:**
```
Treasury_Surplus_t = Treasury_Surplus_{t-1} + Sum(Allocation_{d,t} - Consumption_{d,t})
```

This suggests Treasury_Surplus ACCUMULATES, but this accumulated value is NOT reflected in the core Treasury_t formula. The APPENDIX examples implicitly treat Treasury_Surplus as rolling over into Treasury (not just accumulating separately), which is more consistent with the rollover section.

**Verdict**: INCONSISTENT - 04_ECONOMY_MODEL.md formula is missing Treasury_Surplus term that APPENDIX examples show.

### 2.2 Reward Formula

**09_REWARD_MODEL.md states:**
```
R_t = Base_Reward_t + Productivity_Bonus_t + Efficiency_Bonus_t + Survival_Bonus_t + Allocation_Penalty_t - Bankruptcy_Penalty_t
```

**01_GAME_OVERVIEW.md states:**
> "Reward is global and collective: every agent receives identical reward at every step"
> "Reward = prosperity (GDP per capita) minus penalties for over/under-allocation"

**02_GAME_RULES_REFERENCE.md references:**
> "Efficiency bonus MAY be applied when department consumes less than allocated"

**09_REWARD_MODEL.md defines:**
- `Productivity_Bonus_t = +10 * Treasury_Surplus_t`
- `Efficiency_Bonus_t = +5 * Count(d where Efficiency_Rating_d_t > 1.0)`

**Verdict**: CONSISTENT - Collective reward structure matches across documents.

**Minor Note**: 02_GAME_RULES_REFERENCE.md mentions "Efficiency bonus" but the actual bonus in 09 is based on Efficiency_Rating > 1.0, not just consumption less than allocation. This is a minor semantic difference - the rules reference is simplified.

### 2.3 Voting Rules

**02_GAME_RULES_REFERENCE.md:**
> "A proposal MUST receive a majority of votes to be approved."
> "Majority MUST be defined as more than 50% of non-abstaining votes"
> "A tie in voting MUST result in the proposal being rejected"

**03_TURN_STRUCTURE.md Phase 4:**
> "Simple majority (>50% of non-abstaining votes) required for approval"
> "Tie votes: proposal is rejected"

**05_VOTING_PROTOCOL.md:**
> "More than 50% of non-abstaining votes cast YES"
> "Tie = Rejection: If YES votes equal NO votes among non-abstaining voters, the proposal is REJECTED"
> "Strict majority required (50% + 1 minimum)"

**Verdict**: CONSISTENT - All three documents agree on:
- Majority = >50% of non-abstaining
- Tie = Rejection

### 2.4 Event Visibility

**06_EVENT_SYSTEM.md:**
> "Events MUST reveal severity level to all ministers"
> "Events MUST NOT reveal exact cost impact to ministers"
> "Agents MAY infer approximate cost impact from severity and narrative"

**08_OBSERVATION_SPACE.md:**
> "Agents observe: Event name, Narrative description, Severity level (1–5 scale), Affected department(s)"
> "Agents do NOT observe: exact event cost values"
> "Exact event cost impact (hidden until after round resolves)"

**Verdict**: CONSISTENT - Events reveal severity but hide exact cost.

### 2.5 Surplus Mechanic (Treasury-level vs Department-level)

**01_GAME_OVERVIEW.md:**
> "Treasury-level surplus: Unspent budget returns to the central treasury, incentivizing efficient allocation across all departments"

**02_GAME_RULES_REFERENCE.md:**
> "Unspent allocated budget MUST be returned to the central treasury at end of round"
> "Department surplus is NOT accumulated across rounds (no per-department rollover)"
> "Treasury-level surplus is tracked as total unspent allocation across all departments"

**03_TURN_STRUCTURE.md Phase 8:**
> "Unspent budget from all departments (allocation minus consumption) is calculated"
> "Total unspent amount is credited back to the central treasury as treasury-level surplus"
> "No per-department surplus accumulation occurs"

**04_ECONOMY_MODEL.md:**
> "Treasury_Surplus = Sum(Allocation_d - Consumption_d) (unspent returned to treasury)"
> "Unspent allocation from each department returns to the central treasury"
> "Treasury-level surplus is NOT distributed back to departments"

**APPENDIX_A_EXAMPLES.md:**
> "Treasury receives 80 units back from unspent allocations"
> "Treasury receives 90 units from Round 2 unspent allocations"

**Verdict**: CONSISTENT - All documents correctly specify treasury-level surplus (unspent returns to central treasury, NOT department-level).

---

## 3. CONTRADICTION CHECK

### 3.1 Event Timing

**06_EVENT_SYSTEM.md:**
> "Events are generated at the start of each round (Phase 1 of Turn Structure)"

**03_TURN_STRUCTURE.md Phase 1:**
> "The event system generates 1-N events for the round"
> "Agents do NOT see exact cost impact at this stage"

**03_TURN_STRUCTURE.md Critical Design Notes:**
> "Events BEFORE Proposals: Events are revealed in Phase 1, before any budget proposals in Phase 3"

**Verdict**: CONSISTENT - Events occur before proposals (Phase 1 vs Phase 3).

### 3.2 Revenue Timing

**03_TURN_STRUCTURE.md Phase 7:**
> "Treasury is NOT credited in this phase. Revenue is calculated and stored; it applies next round."

**03_TURN_STRUCTURE.md Critical Design Notes:**
> "Revenue AFTER Consumption: Revenue is calculated in Phase 7 based on efficiency in Phase 6"
> "A department's allocation in round T cannot be offset by revenue that same department generates in round T. Revenue always applies to the NEXT round's treasury calculation."

**04_ECONOMY_MODEL.md:**
> "At the start of each round t (after Phase 7 of round t-1), treasury is calculated"

**Verdict**: CONSISTENT - Revenue applies to NEXT round, not same round.

### 3.3 Bankruptcy Threshold

**02_GAME_RULES_REFERENCE.md:**
> "The episode MUST end immediately if treasury reaches zero or less"

**03_TURN_STRUCTURE.md Phase 9:**
> "if treasury <= 0, episode ends (failure)"

**04_ECONOMY_MODEL.md:**
> "Treasury Bankruptcy: Treasury_t <= 0 at any point during round t"

**10_SUCCESS_CRITERIA.md:**
> "Treasury Bankruptcy: Treasury drops to 0 or below"

**Verdict**: CONSISTENT - All use `<= 0` or equivalent "zero or less".

### 3.4 Majority Definition

**02_GAME_RULES_REFERENCE.md:**
> "Majority MUST be defined as more than 50% of non-abstaining votes"

**05_VOTING_PROTOCOL.md:**
> "Majority required: More than 50% of non-abstaining votes cast YES"
> "Strict majority required (50% + 1 minimum)"

**03_TURN_STRUCTURE.md:**
> "Simple majority (>50% of non-abstaining votes) required for approval"

**Verdict**: CONSISTENT - All specify ">50%" (strict majority).

### 3.5 Surplus Handling

**02_GAME_RULES_REFERENCE.md:**
> "Department surplus is NOT accumulated across rounds"
> "Treasury-level surplus is tracked"

**03_TURN_STRUCTURE.md:**
> "No per-department surplus accumulation occurs"

**04_ECONOMY_MODEL.md:**
> "Treasury-level surplus is NOT distributed back to departments"

**Verdict**: CONSISTENT - Surplus is treasury-level, not department-level.

---

## 4. ADDITIONAL FINDINGS

### 4.1 Efficiency Bonus Discrepancy (Minor)

**02_GAME_RULES_REFERENCE.md:**
> "Efficiency bonus MAY be applied when department consumes less than allocated (efficient under-spending)"

**04_ECONOMY_MODEL.md:**
Does not mention "Efficiency bonus" - only "Efficiency Rating" as a coefficient.

**09_REWARD_MODEL.md:**
> "Efficiency_Bonus_t = +5 * Count(d where Efficiency_Rating_d_t > 1.0)"

The 02 reference to "consumes less than allocated" could mislead implementers. The actual bonus is based on Efficiency_Rating > 1.0, which occurs when Consumption < Allocation, but this is indirect.

**Impact**: Low - implementation would use the formula in 09, but 02's description is simplified.

### 4.2 Treasury Rollover Mechanism (Design Ambiguity)

**04_ECONOMY_MODEL.md "Treasury Surplus Rollover" section:**
```
Treasury_Surplus_t = Treasury_Surplus_{t-1} + Sum(Allocation_{d,t} - Consumption_{d,t})
```

This suggests Treasury_Surplus ACCUMULATES over rounds. But this accumulation doesn't feed back into Treasury_t according to the formula in the same document.

**APPENDIX examples** show Treasury_Surplus being added to Treasury each round, which implies Treasury_Surplus DOES feed back into Treasury (either as a direct addend or via the Productivity Bonus mechanism).

The 04_ECONOMY_MODEL.md definition of Productivity_Bonus:
```
Productivity_Bonus_d = Treasury_Surplus * Efficiency_Rating_d * 0.5
```

This uses Treasury_Surplus (the amount from PREVIOUS round) to calculate bonus that feeds into Treasury_t. So technically Treasury_Surplus affects Treasury indirectly through Productivity_Bonus, not as a direct addend.

**APPENDIX Example 1 Round 2** calculation:
- Treasury_2 = 100 + 47.6 + 988.7 + 80

Where 47.6 = Productivity_Bonus from Round 1 (based on Treasury_Surplus_1 = 80)
And 80 = Treasury_Surplus from Round 1

If Treasury_Surplus only affects Treasury through Productivity_Bonus, why is 80 added separately?

The example appears to add Treasury_Surplus as a DIRECT addend, not just through Productivity_Bonus. This is the inconsistency.

**Impact**: Medium - unclear whether Treasury_Surplus should be added directly to Treasury or only indirectly through Productivity_Bonus.

---

## 5. SUMMARY TABLE

| Check | Status | Evidence |
|-------|--------|----------|
| Glossary term coverage | ⚠️ PARTIAL | 20+ terms missing |
| Treasury formula | ❌ INCONSISTENT | APPENDIX adds Treasury_Surplus; 04 does not include it |
| Reward formula | ✅ CONSISTENT | 01, 02, 09 all align |
| Voting majority | ✅ CONSISTENT | 02, 03, 05 all say >50% |
| Event visibility | ✅ CONSISTENT | 06, 08 align |
| Surplus treasury-level | ✅ CONSISTENT | 01, 02, 03, 04, APPENDIX all correct |
| Event before proposals | ✅ CONSISTENT | Phase 1 vs Phase 3 |
| Revenue next round | ✅ CONSISTENT | Phase 7 timing |
| Bankruptcy <= 0 | ✅ CONSISTENT | All documents |
| Tie = rejection | ✅ CONSISTENT | 02, 05 |

---

## 6. RECOMMENDATIONS

### High Priority

1. **Fix Treasury Formula in 04_ECONOMY_MODEL.md**
   
   Either:
   - **Option A**: Add Treasury_Surplus to the formula:
     ```
     Treasury_t = Baseline_Tax + Productivity_Bonus_{t-1} + Sum(Department_Revenues_{t-1}) + Treasury_Surplus_{t-1}
     ```
   - **Option B**: Clarify that Treasury_Surplus ONLY affects Treasury through Productivity_Bonus, and update APPENDIX examples to not add Treasury_Surplus separately.

2. **Add Missing Terms to Glossary (12_GLOSSARY.md)**
   
   At minimum:
   - `Treasury-level surplus` (with cross-ref to 04)
   - `Efficiency Rating` (with formula cross-ref)
   - `Productivity Multiplier` (with formula cross-ref)
   - `Productivity Bonus` (with cross-ref)
   - `Department Revenue` (with formula cross-ref)
   - `Baselines` definitions (Random, Greedy, Cooperative)

### Medium Priority

3. **Clarify Efficiency Bonus description in 02_GAME_RULES_REFERENCE.md**
   
   Current: "Efficiency bonus MAY be applied when department consumes less than allocated"
   
   Should reference: "Efficiency_Bonus_t in 09_REWARD_MODEL.md is based on Efficiency_Rating > 1.0, which occurs when department consumes less than allocated."

4. **Add Observation Space terms to Glossary or cross-reference**
   
   - `Public Information`
   - `Private Information`  
   - `Hidden Information`

### Low Priority

5. **Add action names to glossary or explicitly cross-reference**
   - PROPOSE_BUDGET, VOTE, DEBATE, ABSTAIN_FROM_PROPOSAL

---

## 7. VERIFICATION EVIDENCE

### Treasury Formula Cross-Reference

| Document | Treasury Formula |
|----------|-----------------|
| 04_ECONOMY_MODEL.md | `Treasury_t = Baseline_Tax + Productivity_Bonus_{t-1} + Sum(Department_Revenues_{t-1})` |
| 02_GAME_RULES_REFERENCE.md | "Treasury MUST receive productivity-based revenue from the previous round" (matches t-1) |
| 03_TURN_STRUCTURE.md | "Revenue is calculated and stored; it applies next round" (confirms t-1) |
| 09_REWARD_MODEL.md | No treasury formula; uses Revenue in prosperity calculation |
| APPENDIX Ex 1 R2 | `100 + 47.6 + 988.7 + 80` = includes Treasury_Surplus |
| APPENDIX Ex 4 R2 | `100 + 45 + 999.8 + 90` = includes Treasury_Surplus |
| APPENDIX Ex 4 R3 | `100 + 27.5 + 903.9 + 55` = includes Treasury_Surplus |

### Event Timing Cross-Reference

| Document | Event Timing |
|----------|-------------|
| 06_EVENT_SYSTEM.md | "generated at the start of each round (Phase 1)" |
| 03_TURN_STRUCTURE.md | Phase 1 = Event Revelation, Phase 3 = Budget Proposal |
| 08_OBSERVATION_SPACE.md | Phase 1 reveals events, cost hidden until after round |

### Voting Cross-Reference

| Document | Majority | Tie |
|----------|----------|-----|
| 02_GAME_RULES_REFERENCE.md | >50% of non-abstaining | Rejection |
| 03_TURN_STRUCTURE.md | >50% of non-abstaining | Rejection |
| 05_VOTING_PROTOCOL.md | >50% of non-abstaining (50%+1 minimum) | Rejection |

### Surplus Cross-Reference

| Document | Surplus Type |
|----------|-------------|
| 01_GAME_OVERVIEW.md | Treasury-level |
| 02_GAME_RULES_REFERENCE.md | Treasury-level (not per-department) |
| 03_TURN_STRUCTURE.md | Treasury-level (no per-department) |
| 04_ECONOMY_MODEL.md | Treasury-level (not distributed back) |
| APPENDIX | Treasury receives unspent back |

---

**End of Report**
