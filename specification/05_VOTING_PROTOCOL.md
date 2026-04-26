# 05 VOTING PROTOCOL

> Defines exact mechanics for voting on budget proposals, including majority calculation, tie-breaking, abstention rules, and edge cases.

---

## Core Voting Mechanics

- Each proposal is voted on independently, in the order submitted during Phase 3
- Proposals are submitted in rotating order (see Phase 3: Budget Proposal Phase in Turn Structure)
- The rotating order ensures no permanent first-mover advantage across rounds
- All ministers MUST vote on each proposal unless they abstain
- Ministers cast one of three votes: YES, NO, or ABSTAIN
- All votes are public and visible to all ministers (who voted what is shown)
- Voting occurs in Phase 4 immediately after all proposals are submitted
- Ministers MUST NOT vote on their own proposal
- Minister voting on own proposal: INVALID, vote is discarded
- Self-voting is prohibited to prevent conflict of interest

---

## Majority Threshold

- **Majority required**: More than 50% of non-abstaining votes cast YES
- Non-abstaining votes = total votes minus abstentions
- Example: 4 YES, 1 NO, 2 ABSTAIN from 7 ministers → 4 YES > 1 NO (majority of 5 non-abstaining)
- Example: 3 YES, 3 NO, 1 ABSTAIN from 7 ministers → tie (3 equals 3), proposal REJECTED

---

## Tie-Breaking Rule

- **Tie = Rejection**: If YES votes equal NO votes among non-abstaining voters, the proposal is REJECTED
- Strict majority required (50% + 1 minimum)
- Tie cannot be broken by random selection or chair casting vote

---

## Abstention Rules

### Proposing (Phase 3)

- **Proposal abstention is removed under Option A.** Every minister MUST submit a `PROPOSE_BUDGET` action each round
- The proposal’s `amount` is **discretionary** (≥ 0). Submitting **0** means “no extra above auto-critical” — it is not an abstention from the phase
- Invalid proposals are rejected as invalid submissions; ministers must correct and resubmit until the phase completes

### Voting (Phase 4)

- A minister MAY abstain from voting on any proposal, including their own
- Abstaining ministers are NOT counted toward the majority threshold calculation
- Abstaining ministers are counted toward quorum (present but not influencing outcome)
- Abstention MUST be an explicit choice (agents must actively choose ABSTAIN rather than default)
- A minister who did not observe a proposal MAY NOT vote on it (must have observed)

---

## Approval Consequences

- **Approved (discretionary)**: In Phase 5 Step 1, treasury is debited by the **approved discretionary amount** for that department (in addition to the Step 0 auto-critical debit for all departments)
- **Approved**: Department total allocation = `Critical_d + Discretionary_d`
- **Rejected**: Department receives **only** auto-critical: `Allocation_d = Critical_d` (mandatory Step 0 still applies); **no** discretionary debit for that department’s rejected ask
- Voting is therefore about **growth funding**, not survival

---

## Rejection Consequences

- Auto-critical debits still apply to all departments when solvent
- Rejected discretionary: department stays at **critical-only** funding; treasury is **not** debited for the rejected discretionary portion
- Rejected proposals cannot be resubmitted in the same round (unless a retry / reopen flow is used by the environment wrapper)
- Department may propose again next round

---

## Debate Rules (Phase 2)

- Ministers MAY engage in public discussion before voting begins
- Debate occurs in Phase 2 (Debate/Discussion Phase), before Phase 3 proposals
- Discussion is OPTIONAL (game proceeds if all ministers skip)
- Ministers can:
  - Share interpretations of event impact
  - Signal budget priorities
  - Form alliances or coalitional positions
- Debate has NO direct mechanical effect on voting outcome
- Debate is unrestricted (no limits on message count or length during Phase 2)

---

## Edge Cases

### All Ministers Abstain from Voting on a Proposal

- Proposal is REJECTED
- No majority possible when all votes are abstentions
- No treasury change occurs

### Tie Vote (YES equals NO among non-abstaining)

- Proposal is REJECTED
- Tie = rejection applies regardless of how many abstentions exist
- Example: 2 YES, 2 NO, 3 ABSTAIN → REJECTED (tie)

### Proposal Exceeds Remaining Treasury

- Proposal is REJECTED automatically BEFORE voting begins
- Check occurs at submission time in Phase 3
- No voting occurs on invalid proposals
- Sequential proposals: if earlier proposals deplete treasury, later proposals may be auto-rejected

### Minister Proposes After Proposal Phase Ends

- Submission is INVALID and IGNORED
- Cannot retroactively submit proposals
- Game rules prohibit late submissions

### Treasury Would Go Negative After Approval

- If an approved proposal would cause treasury to go below zero:
  - The approval stands (approved is approved)
  - Bankruptcy is triggered in Phase 9 (Termination Check Phase)
  - Episode ends immediately

### Sequential Treasury Depletion

- Proposals are processed in submission order
- If early approved proposals deplete treasury:
  - Later proposals in the same round are evaluated against remaining balance
  - Later proposals exceeding remaining balance are auto-rejected
  - This creates strategic pressure around proposal ordering

### All ministers propose zero discretionary

- Every department still receives auto-critical in Phase 5
- Shutdown counter may advance if `sum(Discretionary_d) = 0` for consecutive rounds (see Turn Structure)

### Single Minister Remaining (edge case)

- If only one minister proposes and all others abstain from voting:
  - Their proposal requires YES votes from all non-abstaining (the single voter)
  - If they abstain from their own proposal, it is rejected (zero YES votes)
  - Tie rules apply if multiple ministers vote but YES = NO

---

## Summary Table

| Scenario | Outcome |
|----------|---------|
| YES > 50% of non-abstaining | APPROVED |
| YES = NO (tie) | REJECTED |
| All abstain | REJECTED |
| Proposal exceeds treasury | REJECTED (auto, before voting) |
| Late submission | INVALID (ignored) |
| Minister abstains from voting | Not counted toward majority |
| Minister proposes 0 discretionary | Auto-critical only if approved path allows |

---

## Implementation Notes

- Votes MUST be recorded with timestamp and voter identity
- Vote records are immutable once cast
- Abort early if no proposals exist (skip to Phase 5)
- The voting phase completes only when all non-abstained proposals have been voted upon
