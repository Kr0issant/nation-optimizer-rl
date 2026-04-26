# Option A: Auto-Fund Critical + Discretionary Proposals

## Summary

This PR implements **Option A** from `specification/proposed-amendments/01-critical-threshold-abstention-voting-fix.md`.

**Mechanics:**

- **Phase 5 — Step 0 (auto-critical):** Every department receives `Critical_d = Demand_d × 0.4` before discretionary execution. `sum(Critical_d)` is debited unconditionally. If `Treasury < sum(Critical_d)`, the episode ends with **BANKRUPTCY** (not `CRITICAL_FAILURE`).
- **Phase 3:** Ministers propose **discretionary** amounts ≥ 0 (additional funding above auto-critical). `0` means “critical only.” **Proposal abstention is removed**; every minister must submit `PROPOSE_BUDGET`.
- **Phase 5 — Step 1:** Approved discretionary is added on top of auto-critical. **Rejection** leaves the department at **critical-only** (not zero allocation).
- **Revenue:** RF at exactly critical is **0** (zero revenue from that slice).
- **Shutdown:** Consecutive rounds with **`sum(Discretionary_d) = 0`** (two rounds), not zero total allocation.
- **Termination:** `CRITICAL_FAILURE` is removed. Remaining reasons: **BANKRUPTCY**, **SHUTDOWN**, **MAX_ROUNDS**, **PROSPERITY_THRESHOLD**.
- **Rewards:** No “critical failure” penalty in `compute_reward`. Bankruptcy still applies `BANKRUPTCY_PENALTY` via the `critical_penalty` field on the step breakdown (existing implementation pattern).

**Direct-allocation shortcut:** Still interprets the mapping as desired **total** per department; the engine applies auto-critical first, then discretionary from the remainder. **`StepResult.observation` now snapshots end-of-round state** before the next round’s `_start_round()` resets sector rows (fixes stale allocation in observations).

## Branch note

In this Cursor worktree, Git refused `feature/option-a-critical-auto-fund` because that branch is already checked out in another worktree. This commit is on **`feature/option-a-critical-auto-fund-8fmz`** (or the current HEAD branch at merge time). Rename or cherry-pick onto `feature/option-a-critical-auto-fund` as needed.

## Files changed

| Path | Change |
|------|--------|
| `core/game.py` | Remove `CRITICAL_FAILURE` / critical invariant path; simplify `_finish_round`; `compute_reward` call without critical penalty; direct allocation returns observation snapshot before next `_start_round`; `_result` accepts optional `observation`. |
| `core/reward.py` | Remove critical-failure penalty parameters and logic; document bankruptcy override on `RewardBreakdown.critical_penalty`. |
| `core/parliament.py` | Remove `ProposalAbstention`, `submit_abstention`, and `proposal_abstentions` from resolution state. |
| `core/__init__.py` | Drop `ProposalAbstention` export. |
| `server/models.py` | Remove `ABSTAIN_FROM_PROPOSAL` from `ParliamentaryAction.to_engine_dict`; doc discretionary proposals. |
| `scripts/deep_audit_run.py` | Root-cause printout for **BANKRUPTCY** instead of removed `CRITICAL_FAILURE`. |
| `specification/02_GAME_RULES_REFERENCE.md` | Must propose; auto-critical; discretionary; shutdown on zero discretionary; bankruptcy for unaffordable critical. |
| `specification/03_TURN_STRUCTURE.md` | Phase 5 Step 0/1; Phase 3 mandatory proposals; shutdown counter on discretionary; remove critical-failure phase text. |
| `specification/04_ECONOMY_MODEL.md` | Mandatory vs discretionary; RF=0 at critical; remove `CRITICAL_FAILURE` termination; align tables. |
| `specification/05_VOTING_PROTOCOL.md` | Rejection = critical-only; no proposal abstention. |
| `specification/07_AGENT_ACTION_SPACE.md` | Remove `ABSTAIN_FROM_PROPOSAL`; Phase 3 = `PROPOSE_BUDGET` only. |
| `specification/09_REWARD_MODEL.md` | Remove critical-failure penalty; bankruptcy adjustment; update examples/tables. |
| `specification/10_SUCCESS_CRITERIA.md` | Remove critical failure; shutdown discretionary; termination list. |
| `tests/fixtures/reward_scenarios.py` | Below-critical economy fixture: expect **no** -1000 reward penalty. |
| `tests/integration/test_game_loop.py` | Option A scenarios: auto-critical, zero discretionary, shutdown loop, bankruptcy, direct allocation observation, rejection = critical. |
| `tests/unit/test_action_schema.py` | Assert proposal phase excludes `ABSTAIN_FROM_PROPOSAL`. |
| `tests/unit/test_parliament.py` | Remove unused `ProposalAbstention` import. |
| `tests/unit/test_reward.py` | Remove critical-failure penalty test; assert default `critical_penalty` zero from `compute_reward`. |
| `tests/unit/test_reward_fixtures.py` | Align with reward changes; rename scenario assertion. |
| `PR_DESCRIPTION_OPTION_A.md` | This file. |

## Migration / API notes

- **`ABSTAIN_FROM_PROPOSAL` removed** from the OpenEnv `ParliamentaryAction` mapping. External agents and tools must use **`PROPOSE_BUDGET` with `amount: 0`** instead of abstaining.
- **`ProposalAbstention` removed** from `core.parliament` and package exports. Callers should only use `submit_proposal`.
- **Termination string `CRITICAL_FAILURE`** is no longer produced by `NationGame`. Metrics or dashboards keyed on it should use **BANKRUPTCY** / **SHUTDOWN** / etc.
- **`compute_reward`** no longer accepts `critical_failed` / `critical_failure_occurred` / `critical_penalty_val`.

## Test plan

- `uv sync --extra dev`
- `uv run pytest` (full suite; all tests green in this worktree)

## Intentionally not changed

- `core/revenue.py` (per amendment).
- `training/` (per user request; separate amendment).
