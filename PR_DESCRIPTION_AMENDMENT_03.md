# Amendment 03: Training Specification Alignment

## Summary

This amendment aligns the training pipeline (GRPO reward function, prompts, and rule-based agents) with **Option A** mechanics (auto-fund critical + discretionary proposals). The training code now correctly:

1. Scores proposals based on **total allocation = critical + discretionary** (not just proposal amount)
2. Enforces treasury constraint: `0 ≤ discretionary ≤ (treasury - total_critical)`
3. Uses reduced NO vote penalty magnitude (VOTE_NO_WEIGHT = 0.5)
4. Emphasizes to ministers that they propose **additional** funding above their auto-received critical minimum

## Why This Was Needed

When Option A was implemented in the game engine (auto-funding 40% critical minimum before discretionary proposals), the training pipeline needed corresponding updates:

- **Reward signal**: Must evaluate the full allocation (critical + discretionary), not just the proposed amount
- **Constraints**: Must check discretionary against remaining treasury after critical reservations
- **Prompting**: Ministers need to understand they are competing for residual treasury, not full funding
- **Baselines**: Rule-based agents must emit discretionary amounts, not total allocations

## Files Changed

| File | Change |
|------|--------|
| `schemas/actions.py` | Already clean - no ABSTAIN_FROM_PROPOSAL action |
| `schemas/phases.py` | Already correct - Phase.PROPOSAL only allows PROPOSE_BUDGET |
| `training/reward_fn.py` | Updated to score total allocation (critical + discretionary), enforce (treasury - total_critical) constraint, use VOTE_NO_WEIGHT = 0.5 |
| `llm_integration/prompts/minister.py` | Updated with auto-critical messaging explaining ministers propose discretionary above baseline |
| `agents/rule_based/optimal_zone.py` | Already emits discretionary amounts via `discretionary_for_target_total()` |
| `agents/rule_based/discretionary.py` | Helper module for discretionary calculations |
| `scripts/collect_grpo_prompts.py` | Already records total_critical and uses OptimalZoneAdapter |
| `tests/unit/test_reward_fn.py` | Tests updated for discretionary model |

## Key Implementation Details

### Reward Formula (PROPOSE_BUDGET)
```python
# Total allocation = critical (auto-funded) + discretionary (proposed)
total_allocation = own_sector["critical"] + action.amount
rf = _piecewise_revenue_factor_for_amount(total_allocation, own_sector)
return PROPOSE_BASE_REWARD + PROPOSE_FACTOR_WEIGHT * (rf - 1.0)
```

### Treasury Constraint
```python
total_critical = sum(sector["critical"] for sector in all_sectors.values())
if not 0.0 <= float(action.amount) <= (treasury - total_critical):
    return ILLEGAL_ACTION_REWARD
```

### Vote NO Penalty
```python
if action.vote is VoteChoice.NO:
    return VOTE_NO_WEIGHT * -(rf - 1.0)  # 0.5 magnitude instead of 1.0
```

## Migration Notes

For anyone training models on this codebase:

1. **Prompt datasets**: Regenerate GRPO prompts using `scripts/collect_grpo_prompts.py` to ensure `total_critical` field is present
2. **Reward function**: No changes needed - already uses correct formulas
3. **Baseline adapters**: No changes needed - already emit discretionary amounts
4. **Action parsing**: ABSTAIN_FROM_PROPOSAL is not a valid action type and will return PARSE_FAIL_REWARD

## Verification

```bash
# Run reward function tests
uv run pytest tests/unit/test_reward_fn.py -v

# Verify no ABSTAIN_FROM_PROPOSAL references remain
grep -r "ABSTAIN_FROM_PROPOSAL" --include="*.py" .

# Run full test suite
uv run pytest tests/ -v
```

## Related

- Depends on: Option A implementation (auto-fund critical before discretionary)
- Specification: `specification/proposed-amendments/03-training-spec-alignment.md`
