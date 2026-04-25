# 08 — Observation Space

> Defines exactly what each agent observes at each phase of a round.

---

## Public Information (All Agents See)

The following information is visible to every agent at all times:

- Current treasury balance
- All debate messages exchanged
- All budget proposals made
- All votes cast (including which agent voted what)
- Event ledger (all past events: name, narrative, severity, affected departments)
- Round number and episode progress
- Termination condition status

---

## Private Information (Only Own Department Sees)

Each agent sees the following about their own department only:

- Own department's exact budget allocation (after approval)
- Own department's exact consumption expenditure
- Own department's exact surplus or deficit (current round only, not accumulated)
- Own department's efficiency rating

Agents do NOT see another department's private state.

---

## Hidden Information (From All Agents)

The following is never visible to any agent during the episode:

- Exact event cost impact (hidden until after round resolves)
- Event Base_Cost, Severity_Multiplier, and Random_Variance
- Future events not yet generated
- Internal RNG state
- Other departments' private state (consumption, exact surplus, efficiency rating)

---

## Observation by Phase

### Phase 1: Event Revelation

Agents observe:

- Event ledger update: any new events for this round
  - Event name (e.g., "War", "Virus Outbreak")
  - Narrative description (contextual text)
  - Severity level (1–5 scale)
  - Affected department(s)
- Previous round's final treasury balance
- Previous round's event ledger (full history of past events this episode)

Agents do NOT observe: exact event cost values

---

### Phase 2: Debate

Agents observe:

- Current treasury balance
- All public debate messages from this phase (posted by other agents)
- Own department's current status:
  - Allocated budget from previous round
  - Surplus or deficit carried forward
  - Any events from Phase 1 that affect own department

Agents do NOT observe: other departments' private state

---

### Phase 3: Proposal

Agents observe:

- All proposals made so far in this phase (department, requested amount, submitting agent)
- Current treasury balance remaining
- Own department's current allocation and treasury surplus returned this round
- All past events from the event ledger

Agents do NOT observe: how other agents will vote on proposals not yet submitted

---

### Phase 4: Voting

Agents observe:

- All proposals submitted this round (full list)
- All votes cast so far in this phase
  - Which agent voted YES, NO, or ABSTAIN on each proposal
- Current treasury balance
- Own department's proposal status (if submitted)

Agents do NOT observe: votes not yet cast on current proposals

---

### Phase 5: Budget Execution

Agents observe:

- Final approved proposals and amounts
- Treasury balance after all approved budgets are debited
- Which proposals were approved vs rejected

Agents do NOT observe: any additional information beyond what changed

---

### Phase 6: Consumption and Event Impact

Agents observe:

- Event resolution: exact cost impact of events (revealed after execution)
- Updated event ledger with cost data filled in
- No direct departmental consumption data observed by other agents

Agents observe only: global treasury unchanged, event costs now visible in ledger

Note: Department-level consumption is private to each department. Agents do not see how much another department spent.

---

### Phase 7: Revenue Calculation

Agents observe:

- Updated treasury balance (unchanged this phase)
- Event ledger remains the same
- No revenue figures disclosed to agents this phase

Revenue calculations are internal. Agents learn about revenue through next round's treasury observation.

---

### Phase 8: Treasury Surplus

Agents observe:

- Updated treasury balance (now includes treasury surplus credit)
- Own department's current round surplus/deficit (not accumulated)
- No per-department surplus rollover

Agents do NOT observe: other departments' surplus/deficit amounts

---

### Phase 9: Termination Check

Agents observe:

- Termination status: episode continues or ends
- Final treasury balance (if episode ended)
- Prosperity score (if episode ended)
- Event ledger (complete history)

---

## Observation Format

### Structured Data Format (JSON-like)

Agents receive observations as structured data for programmatic access:

```json
{
  "round": 3,
  "phase": 2,
  "treasury": 850,
  "event_ledger": [
    {
      "round": 1,
      "name": "War",
      "narrative": "Enemy forces have crossed the border...",
      "severity": 4,
      "affected_departments": ["Defense", "Agriculture", "Infrastructure"],
      "cost": 520
    },
    {
      "round": 2,
      "name": "Virus Outbreak",
      "narrative": "A viral outbreak has spread...",
      "severity": 3,
      "affected_departments": ["Health", "Economy"],
      "cost": 380
    },
    {
      "round": 3,
      "name": "Infrastructure Collapse",
      "narrative": "A critical bridge has collapsed...",
      "severity": 3,
      "affected_departments": ["Infrastructure", "Economy", "Defense"],
      "cost": null
    }
  ],
  "proposals": [
    {
      "department": "Defense",
      "amount": 200,
      "status": "approved"
    },
    {
      "department": "Health",
      "amount": 150,
      "status": "approved"
    }
  ],
  "votes": [
    {
      "proposal_department": "Defense",
      "votes": [
        {"agent": "Defense", "vote": "YES"},
        {"agent": "Health", "vote": "YES"},
        {"agent": "Agriculture", "vote": "NO"},
        {"agent": "Economy", "vote": "YES"}
      ]
    }
  ],
  "debate_messages": [
    {
      "agent": "Defense",
      "message": "We need increased allocation due to border tensions."
    },
    {
      "agent": "Health",
      "message": "The virus outbreak will strain our medical supplies."
    }
  ],
  "own_department": {
    "name": "Defense",
    "allocated_budget": 200,
    "consumption": null,
    "surplus": null,
    "efficiency_rating": 0.85,
    "treasury_surplus_returned_this_round": 30
  },
  "termination": {
    "episode_ended": false,
    "reason": null
  }
}
```

### Natural Language Format (For LLM Agents)

Agents receive a human-readable summary alongside structured data:

```
Round 3, Phase 2 (Debate)

Treasury holds 850 units.

Events this round:
- Infrastructure Collapse (Severity: 3)
  A critical bridge has collapsed. Infrastructure repairs required urgently.
  Economic activity slowed. Defense logistics affected.
  Affected: Infrastructure, Economy, Defense

Your department (Defense):
- Previous allocation: 200 units
- Treasury surplus returned this round: 30 units (unspent allocation returned to central treasury)

Debate so far:
- Defense: "We need increased allocation due to border tensions and the bridge collapse logistics impact."
- Health: "The virus outbreak will strain our medical supplies."

Treasury: 850 units (public)

No votes yet. Proposals begin after debate phase.
```

---

## Example Observation: Agent "Health" in Phase 3

### What Health Agent Sees

```json
{
  "round": 2,
  "phase": 3,
  "treasury": 1200,
  "event_ledger": [
    {
      "round": 1,
      "name": "War",
      "narrative": "Enemy forces have crossed the border...",
      "severity": 4,
      "affected_departments": ["Defense", "Agriculture"],
      "cost": 480
    },
    {
      "round": 2,
      "name": "Virus Outbreak",
      "narrative": "A viral outbreak has spread across provinces...",
      "severity": 3,
      "affected_departments": ["Health", "Economy"],
      "cost": null
    }
  ],
  "proposals": [
    {
      "department": "Defense",
      "amount": 300,
      "status": "pending"
    }
  ],
  "own_department": {
    "name": "Health",
    "allocated_budget": 150,
    "consumption": 145,
    "surplus": 5,
    "efficiency_rating": 0.92,
    "treasury_surplus_returned_this_round": 5
  }
}
```

### What Health Agent Does NOT See

- Defense's exact consumption and surplus (private to Defense)
- Defense's efficiency rating (private to Defense)
- Economy department's state (private to Economy)
- Exact cost of Virus Outbreak event (hidden until after round)

---

## Summary: Visibility Matrix

| Information | All Agents See | Own Department Only | Hidden From All |
|------------|----------------|--------------------|----------------|
| Treasury balance | Yes | | |
| Event name, narrative, severity | Yes | | |
| Event exact cost | | | Yes (until after round) |
| All debate messages | Yes | | |
| All proposals | Yes | | |
| All votes | Yes | | |
| Own allocation and surplus | | Yes | |
| Other department's private state | | | Yes |
| Round number | Yes | | |
| Termination status | Yes | | |
