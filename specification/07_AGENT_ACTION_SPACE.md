# 07 AGENT ACTION SPACE

> Defines all valid actions an agent (minister) can take during a round, including constraints, timing, and invalid action handling.

---

## Valid Actions

### 1. PROPOSE_BUDGET

Submit a budget allocation request for the agent's own department.

**Parameters**:
- `department` (string): Must match the agent's assigned portfolio
- `amount` (number): Requested allocation, must be within valid range
- `justification` (string): Narrative explaining the request

**Constraints**:
- `amount` must be >= 0
- `amount` must be <= current treasury balance at submission time
- `amount` must be a numeric value (no strings, nulls, or NaN)
- `department` must be the agent's own assigned department
- One proposal per agent per round (first submission honored, subsequent ignored)

**Timing**: Phase 3 (Budget Proposal Phase) only

**Valid Examples**:
- `{department: "Health", amount: 300, justification: "Medical supplies"}`
- `{department: "Defense", amount: 0, justification: "No needs this round"}`

**Invalid Examples**:
- `{department: "Health", amount: -50, justification: "..."}` — negative amount
- `{department: "Health", amount: 50000, justification: "..."}` — exceeds treasury
- `{department: "Defense", amount: 100, justification: "..."}` — wrong department for agent

**Outcome**:
- Valid proposal: publicly announced, enters voting queue
- Invalid proposal: rejected, agent must resubmit valid amount or abstain

---

### 2. VOTE

Cast a vote on a submitted budget proposal.

**Parameters**:
- `proposal_id` (string): Identifier of the proposal being voted upon
- `vote` (enum): One of YES, NO, ABSTAIN

**Constraints**:
- Must vote on each proposal unless abstaining
- Cannot vote on the same proposal multiple times
- Cannot vote on proposals that do not exist
- Agent must have observed the proposal (been present during its submission)

**Timing**: Phase 4 (Voting Phase) only

**Valid Vote Values**:
- `YES` — support the proposal
- `NO` — oppose the proposal
- `ABSTAIN` — explicit non-participation in vote outcome

**Invalid Examples**:
- `vote` on non-existent proposal_id — ignored
- Duplicate vote on same proposal — second vote ignored
- Vote outside Phase 4 — ignored

**Outcome**:
- YES/NO: vote recorded, influences majority calculation
- ABSTAIN: vote recorded, does not influence majority threshold

---

### 3. DEBATE

Send a public message visible to all agents during discussion phase.

**Parameters**:
- `message` (string): Content of the public announcement

**Constraints**:
- No character limit imposed by game rules
- Message is public (all agents can read)
- No private messaging between agents
- No references to hidden game state

**Timing**: Phase 2 (Debate/Discussion Phase) only

**Usage**:
- Agents MAY send zero, one, or many debate messages
- Debate is optional (game proceeds even if all agents skip)
- Debate has no direct mechanical effect on voting outcome

**Invalid Examples**:
- Debate messages sent outside Phase 2 — ignored
- Private messages — not supported by game design

---

### 4. ABSTAIN_FROM_PROPOSAL

Explicitly skip the agent's turn in the budget proposal phase.

**Parameters**: None required (action is the absence of PROPOSE_BUDGET)

**Constraints**:
- Can only abstain during Phase 3 when it is the agent's turn
- Abstention is explicit (agent must signal intent, not passive default)

**Timing**: Phase 3 (Budget Proposal Phase) only

**Effect**:
- Agent submits no proposal for their department
- Department receives zero allocation for this round
- Treated as rejected proposal (no treasury change)

**Invalid Examples**:
- Abstaining outside Phase 3 — ignored
- Abstaining when it is not the agent's turn — ignored

---

## Phase-Action Mapping

| Phase | Available Actions |
|-------|-------------------|
| Phase 1: Event Revelation | None (observation only) |
| Phase 2: Debate/Discussion | DEBATE |
| Phase 3: Budget Proposal | PROPOSE_BUDGET, ABSTAIN_FROM_PROPOSAL |
| Phase 4: Voting | VOTE |
| Phase 5: Budget Execution | None (system executes) |
| Phase 6: Consumption & Event Impact | None (system executes) |
| Phase 7: Revenue Calculation | None (system executes) |
| Phase 8: Surplus Rollover | None (system executes) |
| Phase 9: Termination Check | None (system executes) |

---

## Invalid Action Handling

### Invalid Amount

**Condition**: `amount` is negative, exceeds treasury balance, or is non-numeric.

**Handling**: Proposal is REJECTED.

- Agent receives error feedback indicating invalid amount
- Agent may resubmit valid proposal or abstain
- No treasury change occurs

**Examples**:
- `-50` — negative rejected
- `1000000` when treasury is `500` — exceeds balance rejected
- `"three hundred"` — non-numeric rejected

---

### Wrong Department

**Condition**: `department` does not match agent's assigned portfolio.

**Handling**: Proposal is REJECTED.

- Agent may resubmit with correct department or abstain

---

### Action Outside Correct Phase

**Condition**: Action is submitted at wrong time (e.g., vote during Phase 3).

**Handling**: Action is IGNORED.

- No penalty applied
- No treasury change
- Game proceeds as if action was not attempted

**Examples**:
- VOTE action in Phase 2 — ignored
- PROPOSE_BUDGET action in Phase 4 — ignored

---

### Multiple Proposals by Same Agent

**Condition**: Agent submits more than one PROPOSE_BUDGET in Phase 3.

**Handling**: Only the first valid proposal is accepted; subsequent submissions are IGNORED.

- Order determined by submission timestamp
- Agent cannot withdraw first proposal to replace with second

---

### Vote on Non-Existent Proposal

**Condition**: `proposal_id` does not match any submitted proposal.

**Handling**: Vote is IGNORED.

- No penalty applied
- Agent may vote on valid proposals

---

### Non-Numeric Amount

**Condition**: `amount` field is not a number (string, null, undefined, NaN).

**Handling**: Proposal is REJECTED.

- Agent may resubmit with valid numeric amount or abstain

---

## State Transitions

```
Agent State: IDLE
  |
  v
Phase 2: Can perform DEBATE
  |
  v
Phase 3: Can perform PROPOSE_BUDGET or ABSTAIN_FROM_PROPOSAL
  |
  v
Phase 4: Can perform VOTE on each proposal in queue
  |
  v
Phase 5+: No actions available (system-driven phases)
```

---

## Summary of Actions

| Action | Parameters | Phase | Constraint |
|--------|------------|-------|------------|
| PROPOSE_BUDGET | department, amount, justification | Phase 3 | 0 <= amount <= treasury |
| VOTE | proposal_id, vote | Phase 4 | proposal must exist |
| DEBATE | message | Phase 2 | none |
| ABSTAIN_FROM_PROPOSAL | none | Phase 3 | must be agent's turn |

---

## Edge Cases

### Agent Submits Invalid Proposal Multiple Times

- First invalid submission: rejected with error
- Subsequent submissions: also rejected until valid or abstain

### Agent Attempts Action During System Phase

- Phase 5-9: all actions ignored
- No penalty, no treasury impact

### Sequential Proposal Depletion Affects Later Proposals

- Earlier approved proposals reduce treasury
- Later proposals evaluated against remaining balance
- If remaining balance < requested amount, later proposal auto-rejected

---

## Implementation Notes

- Actions are atomic (all-or-nothing submission)
- Invalid actions never partially modify state
- Agent must receive feedback for rejected actions
- Re-submission allowed until phase ends or valid submission accepted