# F2 Consistency Check - Learnings

## Task Overview
Performed F2: Consistency Check across all specification documents (01-11 and APPENDIX).

## Key Findings

### 1. Treasury Formula Inconsistency (CRITICAL)
The **Treasury formula in 04_ECONOMY_MODEL.md** does NOT include Treasury_Surplus as a direct addend:
```
Treasury_t = Baseline_Tax + Productivity_Bonus_{t-1} + Sum(Department_Revenues_{t-1})
```

But **APPENDIX_A_EXAMPLES.md** consistently adds Treasury_Surplus separately:
```
Treasury_t = Baseline_Tax + Productivity_Bonus + Department_Revenues + Treasury_Surplus
```

This is a **CRITICAL** inconsistency that needs resolution before implementation.

### 2. Term Coverage Gap
20+ capitalized terms are used across documents but not defined in 12_GLOSSARY.md:
- Treasury-level surplus (critical - central to economy)
- Productivity Multiplier (appears in formula)
- Efficiency Rating (appears in formula)
- Department Revenue (appears in formula)
- Action names (PROPOSE_BUDGET, VOTE, DEBATE, etc.)

### 3. What Was Consistent
The following were consistently documented across all specs:
- Event timing (Phase 1, before proposals Phase 3)
- Revenue timing (applies NEXT round, not same round)
- Bankruptcy threshold (treasury <= 0)
- Majority definition (>50% of non-abstaining)
- Tie = rejection
- Surplus is treasury-level, NOT department-level
- Voting rules
- Event visibility (severity visible, cost hidden)

## Patterns Observed
1. APPENDIX examples often more detailed than core spec formulas
2. When there's inconsistency, examples show behavior (APPENDIX), not the formula (04)
3. Glossary tends to lag behind document正文 (terms added to docs before glossary)

## Recommendations
1. Fix Treasury formula - either update 04 to match APPENDIX or update APPENDIX to not add Treasury_Surplus separately
2. Add Treasury_Surplus, Productivity Multiplier, Efficiency Rating to glossary
3. Consider adding a "defined elsewhere" cross-reference mechanism for formula terms

## Issues Encountered
None - task was purely read-only analysis.
