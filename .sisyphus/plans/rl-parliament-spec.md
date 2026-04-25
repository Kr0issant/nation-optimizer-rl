# RL Parliament Environment — Specification Document Set

## TL;DR

> **Quick Summary**: Create a comprehensive specification folder for a multi-agent RL parliament environment where LLM agents (ministers) cooperatively allocate resources from a central treasury. The spec will serve as the single source of truth before hackathon implementation begins.
> 
> **Deliverables**: 13 markdown specification documents covering game mechanics, economy model, voting protocol, event system, agent action space, observation space, reward model, guardrails, and examples
> - `specification/00_INDEX.md`
> - `specification/01_GAME_OVERVIEW.md`
> - `specification/02_GAME_RULES_REFERENCE.md`
> - `specification/03_TURN_STRUCTURE.md`
> - `specification/04_ECONOMY_MODEL.md`
> - `specification/05_VOTING_PROTOCOL.md`
> - `specification/06_EVENT_SYSTEM.md`
> - `specification/07_AGENT_ACTION_SPACE.md`
> - `specification/08_OBSERVATION_SPACE.md`
> - `specification/09_REWARD_MODEL.md`
> - `specification/10_SUCCESS_CRITERIA.md`
> - `specification/11_GUARDRAILS.md`
> - `specification/12_GLOSSARY.md`
> - `specification/APPENDIX_A_EXAMPLES.md`
> 
> **Estimated Effort**: Medium
> **Parallel Execution**: YES — 3 waves
> **Critical Path**: Game Overview → Game Rules → Turn Structure → Economy → Voting → Event System → Action/Observation Space → Reward → Success Criteria → Guardrails → Glossary → Examples → Index → Final Review

---

## Context

### Original Request
The user is participating in a meta hackathon using Hugging Face as the inference provider, building on Meta's OpenEnv RL framework. They want to build a multi-agent RL environment simulating a parliament/cabinet where LLM agents allocate resources from a central treasury according to Marxist-inspired principles of cooperative resource distribution.

### Interview Summary
**Key Discussions**:
- **Agent Count**: Variable even number (4, 6, 8+) with distinct portfolios
- **Voting**: Sequential proposals with conversation loops; agents can abstain
- **Events**: Stochastic with severity levels + narrative; agents must infer cost impact
- **Surplus**: Rolls over per department; over-allocation is positive-sum if it drives efficiency
- **Reward**: Prosperity / GDP per capita; no debt allowed; bankruptcy = failure
- **Framework**: Meta OpenEnv + Hugging Face LLM inference

### Metis Review
**Identified Gaps** (addressed in plan):
- **Missing docs**: Index, quick reference, action space, observation space, success criteria, guardrails, glossary, examples
- **Ambiguities**: Proposal scope, voting order, event inference mechanics, revenue measurement, tie-breaking, abstention rules, bankruptcy timing
- **Guardrails**: No inter-ministry communication, fixed ministry count, no debt, public voting, budget proposals relative to event timing
- **Pitfalls**: Underspecified action space, invisible state, reward hacking, scale mismatch, tie-breaking ambiguity

---

## Work Objectives

### Core Objective
Produce a complete, unambiguous specification document set that enables any developer to implement the multi-agent RL parliament environment without additional design decisions.

### Concrete Deliverables
- `specification/00_INDEX.md` — Navigation and document map
- `specification/01_GAME_OVERVIEW.md` — Concept, inspiration, and high-level goals
- `specification/02_GAME_RULES_REFERENCE.md` — Single-page rules reference (bullet points)
- `specification/03_TURN_STRUCTURE.md` — Phase-by-phase turn flow
- `specification/04_ECONOMY_MODEL.md` — Treasury, revenue, surplus, bankruptcy
- `specification/05_VOTING_PROTOCOL.md` — Voting mechanics, tie-breaking, abstention
- `specification/06_EVENT_SYSTEM.md` — Event generation, severity, cost inference
- `specification/07_AGENT_ACTION_SPACE.md` — Valid agent actions and constraints
- `specification/08_OBSERVATION_SPACE.md` — What each agent observes
- `specification/09_REWARD_MODEL.md` — Prosperity/GDP calculation
- `specification/10_SUCCESS_CRITERIA.md` — Winning/losing, episode termination
- `specification/11_GUARDRAILS.md` — Explicit exclusions and anti-patterns
- `specification/12_GLOSSARY.md` — Defined terms and concepts
- `specification/APPENDIX_A_EXAMPLES.md` — Example rounds and edge cases

### Definition of Done
- [ ] All 14 documents exist in `specification/` folder
- [ ] Every mechanic is defined without ambiguity (no "TBD")
- [ ] All cross-references between documents are valid
- [ ] Two independent readers would produce equivalent implementations
- [ ] Bullet-point format under subheadings (as requested)

### Must Have
- Complete game loop definition
- Exact treasury and revenue formulas
- Voting protocol with tie-breaking
- Event catalog with severity mechanics
- Agent action enumeration
- Observation space specification
- Reward function formula
- Bankruptcy and termination conditions

### Must NOT Have (Guardrails)
- Implementation code or pseudocode
- "TBD" or "to be determined" placeholders
- Paragraph-style explanations (must be bullet points)
- Ambiguous terms without glossary definitions
- Scope creep into training algorithms or model architecture

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: NO (this is a documentation/spec task)
- **Automated tests**: NO
- **Agent-Executed QA**: YES — verification via file reading, cross-reference checking, consistency audits

### QA Policy
Every task MUST include agent-executed QA scenarios. Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.
- **Documentation**: Read files, verify structure, check cross-references, confirm no "TBD"
- **Consistency**: Verify terms used in one doc are defined in glossary
- **Completeness**: Check that every mechanic mentioned has a home document

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation — can start immediately):
├── Task 1: Create 01_GAME_OVERVIEW.md
├── Task 2: Create 02_GAME_RULES_REFERENCE.md
├── Task 3: Create 03_TURN_STRUCTURE.md
├── Task 4: Create 12_GLOSSARY.md (seed with core terms)
└── Task 5: Create 11_GUARDRAILS.md

Wave 2 (Core Mechanics — after Wave 1):
├── Task 6: Create 04_ECONOMY_MODEL.md
├── Task 7: Create 05_VOTING_PROTOCOL.md
├── Task 8: Create 06_EVENT_SYSTEM.md
├── Task 9: Create 07_AGENT_ACTION_SPACE.md
├── Task 10: Create 08_OBSERVATION_SPACE.md
└── Task 11: Create 09_REWARD_MODEL.md

Wave 3 (Integration & Polish — after Wave 2):
├── Task 12: Create 10_SUCCESS_CRITERIA.md
├── Task 13: Create APPENDIX_A_EXAMPLES.md
├── Task 14: Create 00_INDEX.md
└── Task 15: Final cross-reference and consistency audit

Wave FINAL (Review):
├── Task F1: Oracle compliance audit
├── Task F2: Consistency check across all docs
└── Task F3: Completeness verification
-> Present results -> Get explicit user okay

Critical Path: T1-T5 (Wave 1) → T6-T11 (Wave 2) → T12-T15 (Wave 3) → F1-F3 → user okay
Parallel Speedup: ~60% faster than sequential
Max Concurrent: 6 (Wave 2)
```

### Dependency Matrix

- **T1 (Game Overview)**: None → T2, T3, T4, T5, T6, T7, T8, T9, T10, T11
- **T2 (Game Rules)**: T1 → T6, T7, T8, T9, T10, T11
- **T3 (Turn Structure)**: T1 → T6, T7, T8
- **T4 (Glossary seed)**: None → T6, T7, T8, T9, T10, T11, T12
- **T5 (Guardrails)**: None → T6, T7, T8, T9, T10, T11
- **T6 (Economy)**: T1, T2, T3, T4, T5 → T9, T10, T11, T12
- **T7 (Voting)**: T1, T2, T3, T4, T5 → T9, T11, T12
- **T8 (Events)**: T1, T2, T3, T4, T5 → T9, T10, T11
- **T9 (Action Space)**: T1-T8 → T10, T11, T12
- **T10 (Observation)**: T1-T9 → T11, T12
- **T11 (Reward)**: T1-T10 → T12
- **T12 (Success Criteria)**: T1-T11 → T13, T14
- **T13 (Examples)**: T1-T12 → T14
- **T14 (Index)**: T1-T13 → T15
- **T15 (Audit)**: T1-T14 → F1-F3

### Agent Dispatch Summary

- **Wave 1**: 5 tasks → all `quick` (documentation writing)
- **Wave 2**: 6 tasks → all `quick` (documentation writing)
- **Wave 3**: 4 tasks → all `quick` (documentation writing + audit)
- **FINAL**: 3 tasks → F1 `oracle`, F2 `unspecified-high`, F3 `unspecified-high`

---

## TODOs

- [x] 1. **Create 01_GAME_OVERVIEW.md**

  **What to do**:
  - Write the high-level concept document covering: project inspiration (Marxist doctrine), core premise (ministers allocating resources), agent count (variable even number), and the "no corruption" principle (agents trained for collective reward)
  - Include sections: Concept, Inspiration, Goals, Target Audience (hackathon team), Non-Goals (what this system is NOT)
  - Keep to 1-2 pages max

  **Must NOT do**:
  - Include implementation details or code
  - Go into mechanic details (save for Game Rules doc)
  - Use paragraphs without bullet points

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Pure documentation writing task requiring clear, persuasive prose
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4, 5)
  - **Blocks**: Tasks 2, 6, 7, 8, 9, 10, 11, 12, 13
  - **Blocked By**: None

  **References**:
  - `specification/02_GAME_RULES_REFERENCE.md` (will be created in Task 2) — cross-reference for "see Game Rules for mechanics"

  **Acceptance Criteria**:
  - [ ] File exists at `specification/01_GAME_OVERVIEW.md`
  - [ ] Contains bullet points under subheadings (not paragraph-only)
  - [ ] Covers: Concept, Inspiration, Goals, Non-Goals
  - [ ] Mentions Marxist doctrine and cooperative resource allocation
  - [ ] Mentions variable even agent count
  - [ ] No "TBD" or ambiguous placeholders

  **QA Scenarios**:

  ```
  Scenario: Document structure is correct
    Tool: Bash (cat)
    Preconditions: File has been written
    Steps:
      1. Read `specification/01_GAME_OVERVIEW.md`
      2. Verify file contains "## Concept", "## Inspiration", "## Goals"
      3. Verify at least 80% of content is bullet points (not paragraphs)
    Expected Result: Structure matches acceptance criteria
    Evidence: .sisyphus/evidence/task-1-structure-check.txt
  ```

  **Evidence to Capture**:
  - [ ] File structure evidence: task-1-structure-check.txt

  **Commit**: YES
  - Message: `docs(spec): add game overview`
  - Files: `specification/01_GAME_OVERVIEW.md`

- [x] 2. **Create 02_GAME_RULES_REFERENCE.md**

  **What to do**:
  - Write the single-page quick reference for ALL game mechanics
  - Include: agent roles, treasury rules, budget proposal rules, voting rules, event rules, bankruptcy rules, surplus rules
  - Use "MUST", "MUST NOT", "MAY" language for requirements
  - This is the anchor document that other specs reference

  **Must NOT do**:
  - Include turn-by-turn flow (save for Turn Structure doc)
  - Include event catalog (save for Event System doc)
  - Include formulas (save for Economy/Reward docs)

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Requires precise, rules-lawyer-grade documentation
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4, 5)
  - **Blocks**: Tasks 6, 7, 8, 9, 10, 11, 12
  - **Blocked By**: Task 1 (for consistency with Overview)

  **References**:
  - `specification/01_GAME_OVERVIEW.md` — align with high-level concept

  **Acceptance Criteria**:
  - [ ] File exists at `specification/02_GAME_RULES_REFERENCE.md`
  - [ ] Covers all game mechanics in bullet-point format
  - [ ] Uses "MUST/MUST NOT/MAY" language
  - [ ] No mechanics are undefined or ambiguous
  - [ ] Includes at least one "Example:" bullet for complex rules

  **QA Scenarios**:

  ```
  Scenario: Rules are comprehensive and unambiguous
    Tool: Bash (cat + grep)
    Preconditions: File has been written
    Steps:
      1. Read file and search for "MUST" — should find ≥10 occurrences
      2. Verify no "TBD", "to be determined", "TODO" strings exist
      3. Verify file contains sections for: Agents, Treasury, Voting, Events, Bankruptcy
    Expected Result: All mechanics present, zero ambiguity markers
    Evidence: .sisyphus/evidence/task-2-rules-check.txt
  ```

  **Evidence to Capture**:
  - [ ] Rules completeness evidence: task-2-rules-check.txt

  **Commit**: YES
  - Message: `docs(spec): add game rules reference`
  - Files: `specification/02_GAME_RULES_REFERENCE.md`

- [x] 3. **Create 03_TURN_STRUCTURE.md**

  **What to do**:
  - Define the exact phase-by-phase flow of a single game turn/round
  - Include: event revelation phase, proposal phase, voting phase, execution phase, revenue calculation phase
  - Specify order of operations (e.g., events happen BEFORE or AFTER proposals?)
  - Include diagram or numbered list showing exact sequence

  **Must NOT do**:
  - Include event catalog details (save for Event System doc)
  - Include voting tie-breaking (save for Voting Protocol doc)
  - Include revenue formulas (save for Economy doc)

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Requires precise sequencing documentation
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4, 5)
  - **Blocks**: Tasks 6, 7, 8
  - **Blocked By**: Task 1

  **References**:
  - `specification/02_GAME_RULES_REFERENCE.md` — align with rules

  **Acceptance Criteria**:
  - [ ] File exists at `specification/03_TURN_STRUCTURE.md`
  - [ ] Defines exact sequence of phases per turn
  - [ ] Specifies whether events are revealed before or after proposals
  - [ ] Includes timing of revenue calculation relative to allocation
  - [ ] Bullet-point format under phase subheadings

  **QA Scenarios**:

  ```
  Scenario: Turn sequence is fully specified
    Tool: Bash (cat + grep)
    Preconditions: File has been written
    Steps:
      1. Read file and verify it contains numbered or ordered phases
      2. Verify "event" and "proposal" order is explicit (which comes first)
      3. Verify "revenue" and "allocation" order is explicit
    Expected Result: No ambiguity in phase ordering
    Evidence: .sisyphus/evidence/task-3-turn-check.txt
  ```

  **Evidence to Capture**:
  - [ ] Turn structure evidence: task-3-turn-check.txt

  **Commit**: YES
  - Message: `docs(spec): add turn structure`
  - Files: `specification/03_TURN_STRUCTURE.md`

- [x] 4. **Create 12_GLOSSARY.md (seed)**

  **What to do**:
  - Create the glossary with core terms that will be referenced across all docs
  - Include: Treasury, Budget, Proposal, Vote, Event, Severity, Surplus, Bankruptcy, Prosperity, Productivity, Minister, Department, Term, Episode
  - Each term gets a 1-2 sentence definition
  - Mark terms as "[TBD — will be expanded in Wave 3]" only if they depend on mechanics not yet written

  **Must NOT do**:
  - Include terms that don't appear in other documents
  - Write essays for definitions

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Simple reference documentation
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 5)
  - **Blocks**: Tasks 6, 7, 8, 9, 10, 11, 12
  - **Blocked By**: None

  **References**:
  - `specification/01_GAME_OVERVIEW.md` — extract key concepts
  - `specification/02_GAME_RULES_REFERENCE.md` — extract technical terms

  **Acceptance Criteria**:
  - [ ] File exists at `specification/12_GLOSSARY.md`
  - [ ] Contains ≥15 defined terms
  - [ ] Each definition is 1-2 sentences max
  - [ ] Terms are alphabetically sorted
  - [ ] Bullet-point format

  **QA Scenarios**:

  ```
  Scenario: Glossary is comprehensive and organized
    Tool: Bash (cat + grep + wc)
    Preconditions: File has been written
    Steps:
      1. Count defined terms (grep "^-") — should be ≥15
      2. Verify alphabetical order by reading first letters
      3. Verify average definition length is ≤2 sentences
    Expected Result: Reference-ready glossary
    Evidence: .sisyphus/evidence/task-4-glossary-check.txt
  ```

  **Evidence to Capture**:
  - [ ] Glossary evidence: task-4-glossary-check.txt

  **Commit**: YES
  - Message: `docs(spec): add glossary seed`
  - Files: `specification/12_GLOSSARY.md`

- [x] 5. **Create 11_GUARDRAILS.md**

  **What to do**:
  - Document explicit exclusions and anti-patterns
  - Include: no inter-ministry communication, fixed ministry count per episode, no debt/borrowing, single treasury, public voting, no secret ballots, no agent removal mid-episode, maximum events per episode, reward = aggregate not individual
  - For each guardrail: explain WHY it exists (prevents scope creep, prevents complexity explosion)
  - Include "AI Slop Patterns to Avoid" section

  **Must NOT do**:
  - Include positive requirements (save for other docs)
  - Be vague ("don't make it too complex") — be specific

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Requires clear, enforceable constraint documentation
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 4)
  - **Blocks**: Tasks 6, 7, 8, 9, 10, 11
  - **Blocked By**: None

  **References**:
  - Metis review findings (guardrails section)

  **Acceptance Criteria**:
  - [ ] File exists at `specification/11_GUARDRAILS.md`
  - [ ] Contains ≥10 explicit guardrails
  - [ ] Each guardrail has a "Why:" explanation
  - [ ] Includes "AI Slop Patterns to Avoid" section
  - [ ] Bullet-point format

  **QA Scenarios**:

  ```
  Scenario: Guardrails are explicit and justified
    Tool: Bash (cat + grep)
    Preconditions: File has been written
    Steps:
      1. Count "MUST NOT" or "NO " statements — should be ≥10
      2. Verify each has a "Why:" explanation nearby
      3. Verify "AI Slop" section exists
    Expected Result: Enforceable constraints documented
    Evidence: .sisyphus/evidence/task-5-guardrails-check.txt
  ```

  **Evidence to Capture**:
  - [ ] Guardrails evidence: task-5-guardrails-check.txt

  **Commit**: YES
  - Message: `docs(spec): add guardrails`
  - Files: `specification/11_GUARDRAILS.md`

- [x] 6. **Create 04_ECONOMY_MODEL.md**

  **What to do**:
  - Define the complete economic model: treasury formula, baseline tax revenue, productivity-based revenue, departmental surplus rollover
  - Include formulas (e.g., `Treasury_t = Baseline + Productivity_{t-1} + Sum(Department_Revenues)`)
  - Define how departmental efficiency translates to revenue generation
  - Specify bankruptcy condition exactly (treasury ≤ 0? < 0?)
  - Define starting treasury amount

  **Must NOT do**:
  - Include reward formulas (save for Reward Model doc)
  - Include event costs (save for Event System doc)
  - Be vague about formulas

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Requires precise mathematical documentation
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 7, 8, 9, 10, 11)
  - **Blocks**: Tasks 9, 10, 11, 12
  - **Blocked By**: Tasks 1, 2, 3, 4, 5

  **References**:
  - `specification/02_GAME_RULES_REFERENCE.md` — align with rules
  - `specification/03_TURN_STRUCTURE.md` — align with phase timing
  - `specification/12_GLOSSARY.md` — use defined terms

  **Acceptance Criteria**:
  - [ ] File exists at `specification/04_ECONOMY_MODEL.md`
  - [ ] Contains exact formulas for treasury calculation
  - [ ] Defines baseline revenue amount or formula
  - [ ] Defines how productivity affects next-step revenue
  - [ ] Defines surplus rollover mechanics
  - [ ] Defines bankruptcy threshold
  - [ ] Bullet-point format with formula subheadings

  **QA Scenarios**:

  ```
  Scenario: Economy formulas are exact and consistent
    Tool: Bash (cat + grep)
    Preconditions: File has been written
    Steps:
      1. Verify file contains "=" symbols for formulas
      2. Verify "bankruptcy" threshold is a specific number or condition
      3. Verify "surplus" rollover is explicitly defined
    Expected Result: Formulas are implementable without interpretation
    Evidence: .sisyphus/evidence/task-6-economy-check.txt
  ```

  **Evidence to Capture**:
  - [ ] Economy formulas evidence: task-6-economy-check.txt

  **Commit**: YES
  - Message: `docs(spec): add economy model`
  - Files: `specification/04_ECONOMY_MODEL.md`

- [x] 7. **Create 05_VOTING_PROTOCOL.md**

  **What to do**:
  - Define exact voting mechanics: proposal format, voting order, majority threshold, tie-breaking rule
  - Define abstention rules (can agents abstain from proposing? from voting?)
  - Define what happens on approval vs rejection
  - Define conversation loop mechanics (can agents debate before voting?)
  - Include edge cases: all abstain, tie vote, proposal exceeds remaining treasury

  **Must NOT do**:
  - Include proposal content rules (save for Action Space doc)
  - Include agent reasoning (save for implementation)

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Requires precise protocol documentation
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 8, 9, 10, 11)
  - **Blocks**: Tasks 9, 11, 12
  - **Blocked By**: Tasks 1, 2, 3, 4, 5

  **References**:
  - `specification/02_GAME_RULES_REFERENCE.md` — align with rules
  - `specification/03_TURN_STRUCTURE.md` — align with turn phases

  **Acceptance Criteria**:
  - [ ] File exists at `specification/05_VOTING_PROTOCOL.md`
  - [ ] Defines majority threshold (e.g., >50%, ≥50%)
  - [ ] Defines tie-breaking rule
  - [ ] Defines abstention rules for proposing and voting
  - [ ] Defines approval/rejection consequences
  - [ ] Covers edge cases (all abstain, tie, exceeds treasury)
  - [ ] Bullet-point format

  **QA Scenarios**:

  ```
  Scenario: Voting protocol is unambiguous
    Tool: Bash (cat + grep)
    Preconditions: File has been written
    Steps:
      1. Verify "majority" is defined with exact threshold
      2. Verify "tie" is addressed with specific rule
      3. Verify "abstain" is addressed for both proposing and voting
      4. Verify edge case section exists
    Expected Result: All voting scenarios have defined outcomes
    Evidence: .sisyphus/evidence/task-7-voting-check.txt
  ```

  **Evidence to Capture**:
  - [ ] Voting protocol evidence: task-7-voting-check.txt

  **Commit**: YES
  - Message: `docs(spec): add voting protocol`
  - Files: `specification/05_VOTING_PROTOCOL.md`

- [x] 8. **Create 06_EVENT_SYSTEM.md**

  **What to do**:
  - Define event generation: frequency (guaranteed per round? probabilistic?), event types, severity levels
  - Create an event catalog with examples: war, famine, breakthroughs, virus outbreak, etc.
  - Define how severity maps to cost impact (formula or table)
  - Define what agents see (narrative + severity) vs what is hidden (exact cost)
  - Define event relevancy per department (which events affect which ministries)

  **Must NOT do**:
  - Include agent inference strategy (save for implementation)
  - Include all possible events (provide examples + generation rules)

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Requires structured catalog documentation
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 7, 9, 10, 11)
  - **Blocks**: Tasks 9, 10, 11
  - **Blocked By**: Tasks 1, 2, 3, 4, 5

  **References**:
  - `specification/02_GAME_RULES_REFERENCE.md` — align with rules
  - `specification/04_ECONOMY_MODEL.md` — align with cost impact on treasury

  **Acceptance Criteria**:
  - [ ] File exists at `specification/06_EVENT_SYSTEM.md`
  - [ ] Defines event frequency/generation rules
  - [ ] Contains event catalog with ≥5 example events
  - [ ] Defines severity levels and their meaning
  - [ ] Defines what agents observe vs what is hidden
  - [ ] Defines department relevancy for events
  - [ ] Bullet-point format with event subheadings

  **QA Scenarios**:

  ```
  Scenario: Event system is comprehensive
    Tool: Bash (cat + grep)
    Preconditions: File has been written
    Steps:
      1. Count example events — should be ≥5
      2. Verify "severity" is defined with levels
      3. Verify "hidden" or "agent sees" is explicitly stated
      4. Verify event frequency is defined
    Expected Result: Complete event generation and impact specification
    Evidence: .sisyphus/evidence/task-8-events-check.txt
  ```

  **Evidence to Capture**:
  - [ ] Event system evidence: task-8-events-check.txt

  **Commit**: YES
  - Message: `docs(spec): add event system`
  - Files: `specification/06_EVENT_SYSTEM.md`

- [x] 9. **Create 07_AGENT_ACTION_SPACE.md**

  **What to do**:
  - Enumerate ALL valid actions an agent can take
  - Include: propose budget (with amount), vote (yes/no/abstain), debate/communicate (if enabled)
  - Define action constraints: max proposal amount, proposal format, timing restrictions
  - Define what happens on invalid actions
  - Include state-action mapping (what can agent do in each phase)

  **Must NOT do**:
  - Include LLM prompt design (save for implementation)
  - Include reasoning strategy (save for implementation)

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Requires exhaustive enumeration
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 7, 8, 10, 11)
  - **Blocks**: Tasks 10, 11, 12
  - **Blocked By**: Tasks 1, 2, 3, 4, 5, 6, 7, 8

  **References**:
  - `specification/02_GAME_RULES_REFERENCE.md` — align with rules
  - `specification/05_VOTING_PROTOCOL.md` — align with voting actions
  - `specification/03_TURN_STRUCTURE.md` — align with phase restrictions

  **Acceptance Criteria**:
  - [ ] File exists at `specification/07_AGENT_ACTION_SPACE.md`
  - [ ] Enumerates ALL valid actions
  - [ ] Defines action constraints (amount limits, timing)
  - [ ] Defines invalid action handling
  - [ ] Maps actions to turn phases
  - [ ] Bullet-point format

  **QA Scenarios**:

  ```
  Scenario: Action space is fully enumerated
    Tool: Bash (cat + grep)
    Preconditions: File has been written
    Steps:
      1. List all action types mentioned in file
      2. Verify each has constraints defined
      3. Verify "invalid" action handling is specified
    Expected Result: Complete action enumeration
    Evidence: .sisyphus/evidence/task-9-action-check.txt
  ```

  **Evidence to Capture**:
  - [ ] Action space evidence: task-9-action-check.txt

  **Commit**: YES
  - Message: `docs(spec): add agent action space`
  - Files: `specification/07_AGENT_ACTION_SPACE.md`

- [x] 10. **Create 08_OBSERVATION_SPACE.md**

  **What to do**:
  - Define exactly what each agent observes at each phase
  - Include: treasury amount (full or partial?), own department status, event ledger, previous round history, other agents' proposals/votes
  - Define information asymmetry: what is public vs private
  - Define observation format (structured JSON? natural language?)
  - Include examples of what an agent "sees" in a typical round

  **Must NOT do**:
  - Include prompt engineering (save for implementation)
  - Include hidden state that agents DON'T see (save for Event System)

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Requires precise interface documentation
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 7, 8, 9, 11)
  - **Blocks**: Tasks 11, 12
  - **Blocked By**: Tasks 1, 2, 3, 4, 5, 6, 7, 8, 9

  **References**:
  - `specification/02_GAME_RULES_REFERENCE.md` — align with information rules
  - `specification/06_EVENT_SYSTEM.md` — align with event visibility
  - `specification/05_VOTING_PROTOCOL.md` — align with public vs private votes

  **Acceptance Criteria**:
  - [ ] File exists at `specification/08_OBSERVATION_SPACE.md`
  - [ ] Defines observation for each turn phase
  - [ ] Distinguishes public vs private information
  - [ ] Includes example observation
  - [ ] Defines observation format
  - [ ] Bullet-point format

  **QA Scenarios**:

  ```
  Scenario: Observation space is fully specified
    Tool: Bash (cat + grep)
    Preconditions: File has been written
    Steps:
      1. Verify file lists all observable quantities
      2. Verify "public" and "private" are distinguished
      3. Verify example observation is present
    Expected Result: Complete observation specification
    Evidence: .sisyphus/evidence/task-10-observation-check.txt
  ```

  **Evidence to Capture**:
  - [ ] Observation space evidence: task-10-observation-check.txt

  **Commit**: YES
  - Message: `docs(spec): add observation space`
  - Files: `specification/08_OBSERVATION_SPACE.md`

- [x] 11. **Create 09_REWARD_MODEL.md**

  **What to do**:
  - Define the exact reward function formula for "prosperity" / GDP per capita
  - Include: base reward, productivity bonus, efficiency bonus, survival bonus, penalty for over/under-allocation
  - Define reward scope: is it per-agent or global/collective?
  - Define reward timing: per-step or per-episode?
  - Include examples of reward calculation for different scenarios

  **Must NOT do**:
  - Include training strategy (save for implementation)
  - Be vague about "prosperity" — define it mathematically

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Requires precise mathematical documentation
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 7, 8, 9, 10)
  - **Blocks**: Tasks 12
  - **Blocked By**: Tasks 1, 2, 3, 4, 5, 6, 7, 8, 9, 10

  **References**:
  - `specification/04_ECONOMY_MODEL.md` — align with revenue/productivity
  - `specification/02_GAME_RULES_REFERENCE.md` — align with reward rules

  **Acceptance Criteria**:
  - [ ] File exists at `specification/09_REWARD_MODEL.md`
  - [ ] Contains exact reward formula(s)
  - [ ] Defines "prosperity" mathematically
  - [ ] Specifies per-step vs per-episode rewards
  - [ ] Specifies individual vs collective reward
  - [ ] Includes example calculations
  - [ ] Bullet-point format

  **QA Scenarios**:

  ```
  Scenario: Reward function is exact and unambiguous
    Tool: Bash (cat + grep)
    Preconditions: File has been written
    Steps:
      1. Verify file contains "=" for reward formula
      2. Verify "prosperity" or "GDP" is mathematically defined
      3. Verify individual vs collective reward is stated
      4. Verify example calculation exists
    Expected Result: Reward is implementable without interpretation
    Evidence: .sisyphus/evidence/task-11-reward-check.txt
  ```

  **Evidence to Capture**:
  - [ ] Reward model evidence: task-11-reward-check.txt

  **Commit**: YES
  - Message: `docs(spec): add reward model`
  - Files: `specification/09_REWARD_MODEL.md`

- [x] 12. **Create 10_SUCCESS_CRITERIA.md**

  **What to do**:
  - Define winning/losing conditions: episode termination triggers (bankruptcy, max rounds, prosperity threshold)
  - Define success metrics: what does a "good" run look like?
  - Include: survival time, final prosperity score, budget balance quality
  - Define episode boundaries: when does an episode start and end?
  - Include comparison baselines: random agent performance, greedy agent performance

  **Must NOT do**:
  - Include evaluation code (save for implementation)
  - Include leaderboards or competitive metrics

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Requires clear success/failure definition
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 13, 14, 15)
  - **Blocks**: Tasks 13, 14
  - **Blocked By**: Tasks 1-11

  **References**:
  - `specification/04_ECONOMY_MODEL.md` — align with bankruptcy condition
  - `specification/09_REWARD_MODEL.md` — align with prosperity metric

  **Acceptance Criteria**:
  - [ ] File exists at `specification/10_SUCCESS_CRITERIA.md`
  - [ ] Defines all episode termination conditions
  - [ ] Defines success metrics with thresholds
  - [ ] Includes baseline comparisons
  - [ ] Defines episode start/end boundaries
  - [ ] Bullet-point format

  **QA Scenarios**:

  ```
  Scenario: Success criteria are fully defined
    Tool: Bash (cat + grep)
    Preconditions: File has been written
    Steps:
      1. Verify "termination" or "end" conditions are listed
      2. Verify success metrics have thresholds
      3. Verify baseline comparisons are included
    Expected Result: Clear win/lose/success definition
    Evidence: .sisyphus/evidence/task-12-success-check.txt
  ```

  **Evidence to Capture**:
  - [ ] Success criteria evidence: task-12-success-check.txt

  **Commit**: YES
  - Message: `docs(spec): add success criteria`
  - Files: `specification/10_SUCCESS_CRITERIA.md`

- [x] 13. **Create APPENDIX_A_EXAMPLES.md**

  **What to do**:
  - Provide 2-3 complete example rounds showing the game in action
  - Each example: starting state, events, proposals, votes, outcomes, final state
  - Include edge case examples: bankruptcy round, all-abstain vote, surplus rollover
  - Show how events affect different departments differently
  - Use concrete numbers (e.g., "Treasury starts at 1000, Health proposes 300...")

  **Must NOT do**:
  - Include hypothetical scenarios that violate rules
  - Be vague about numbers

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Requires concrete scenario writing
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 12, 14, 15)
  - **Blocks**: Task 14
  - **Blocked By**: Tasks 1-12

  **References**:
  - `specification/02_GAME_RULES_REFERENCE.md` — follow all rules exactly
  - `specification/03_TURN_STRUCTURE.md` — follow turn phases exactly
  - `specification/04_ECONOMY_MODEL.md` — use exact formulas
  - `specification/05_VOTING_PROTOCOL.md` — follow voting rules
  - `specification/06_EVENT_SYSTEM.md` — use example events

  **Acceptance Criteria**:
  - [ ] File exists at `specification/APPENDIX_A_EXAMPLES.md`
  - [ ] Contains ≥2 complete example rounds
  - [ ] Contains ≥1 edge case example
  - [ ] Uses concrete numbers for all values
  - [ ] Follows all rules from other documents exactly
  - [ ] Bullet-point format with round subheadings

  **QA Scenarios**:

  ```
  Scenario: Examples are complete and consistent
    Tool: Bash (cat + grep)
    Preconditions: File has been written
    Steps:
      1. Count complete example rounds — should be ≥2
      2. Verify edge case section exists
      3. Verify all numbers are concrete (no "some amount")
      4. Cross-check one example against rules docs for consistency
    Expected Result: Examples illustrate mechanics without ambiguity
    Evidence: .sisyphus/evidence/task-13-examples-check.txt
  ```

  **Evidence to Capture**:
  - [ ] Examples evidence: task-13-examples-check.txt

  **Commit**: YES
  - Message: `docs(spec): add appendix examples`
  - Files: `specification/APPENDIX_A_EXAMPLES.md`

- [x] 14. **Create 00_INDEX.md**

  **What to do**:
  - Create the navigation document listing all spec files with one-line summaries
  - Include: document map, reading order, version info, last updated date
  - Add quick-links to each document
  - Include a "How to Use This Spec" section for hackathon team

  **Must NOT do**:
  - Include content that belongs in other docs
  - Be just a table of contents (add guidance on how to read)

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Simple navigation document
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 12, 13, 15)
  - **Blocks**: Task 15
  - **Blocked By**: Tasks 1-13

  **References**:
  - All other specification documents — reference each

  **Acceptance Criteria**:
  - [ ] File exists at `specification/00_INDEX.md`
  - [ ] Lists all 14 documents with one-line summaries
  - [ ] Includes recommended reading order
  - [ ] Includes "How to Use This Spec" section
  - [ ] Bullet-point format

  **QA Scenarios**:

  ```
  Scenario: Index is complete and navigable
    Tool: Bash (cat + grep)
    Preconditions: File has been written
    Steps:
      1. Count listed documents — should be 14
      2. Verify each has a one-line summary
      3. Verify reading order is suggested
    Expected Result: Complete navigation document
    Evidence: .sisyphus/evidence/task-14-index-check.txt
  ```

  **Evidence to Capture**:
  - [ ] Index evidence: task-14-index-check.txt

  **Commit**: YES
  - Message: `docs(spec): add index`
  - Files: `specification/00_INDEX.md`

- [x] 15. **Final Cross-Reference and Consistency Audit**

  **What to do**:
  - Read all specification documents
  - Verify every cross-reference resolves (e.g., "see Economy Model" links to actual doc)
  - Verify all terms used are in glossary
  - Verify formulas are consistent across docs
  - Verify no contradictions exist between documents
  - Fix any inconsistencies found
  - Update glossary with any missing terms discovered during audit

  **Must NOT do**:
  - Skip inconsistencies (fix them or flag for user decision)
  - Add new mechanics not in other docs

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Requires careful cross-document analysis
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 12, 13, 14)
  - **Blocks**: F1, F2, F3
  - **Blocked By**: Tasks 1-14

  **References**:
  - All specification documents

  **Acceptance Criteria**:
  - [ ] All cross-references verified and resolving
  - [ ] All terms in glossary
  - [ ] Formulas consistent across docs
  - [ ] Zero contradictions found
  - [ ] Audit report saved to `.sisyphus/evidence/task-15-audit-report.md`

  **QA Scenarios**:

  ```
  Scenario: Cross-reference consistency
    Tool: Bash (grep + manual check)
    Preconditions: All docs exist
    Steps:
      1. Search for "see" or "refer to" in all docs
      2. Verify each referenced document exists
      3. Compare treasury formula in Economy vs Reward docs
      4. Verify glossary contains all capitalized terms
    Expected Result: Zero broken references, zero formula mismatches
    Evidence: .sisyphus/evidence/task-15-audit-report.md
  ```

  **Evidence to Capture**:
  - [ ] Audit report: task-15-audit-report.md

  **Commit**: YES
  - Message: `docs(spec): cross-reference audit and fixes`
  - Files: All updated specification documents

---

## Final Verification Wave

> 3 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**

- [x] F1. **Plan Compliance Audit** — `oracle`

  **What to do**:
  - Read the plan end-to-end
  - For each "Must Have": verify the spec document exists and contains the required section
  - For each "Must NOT Have": search all docs for forbidden patterns ("TBD", "to be determined", paragraph-only docs, code blocks)
  - Check that all cross-references resolve
  - Compare deliverables against plan

  **Acceptance Criteria**:
  - [ ] All 14 specification documents exist
  - [ ] Zero "TBD" or "to be determined" strings found
  - [ ] Zero paragraph-only documents (bullet points verified)
  - [ ] All cross-references resolve to existing files
  - [ ] All "Must Have" items present in docs
  - [ ] All "Must NOT Have" items absent from docs

  **QA Scenarios**:

  ```
  Scenario: Verify compliance with plan requirements
    Tool: Bash (find, grep, wc)
    Preconditions: All tasks complete
    Steps:
      1. `find specification/ -name "*.md" | wc -l` → Expected: 14
      2. `grep -ri "TBD\|to be determined\|TODO\|FIXME" specification/` → Expected: empty
      3. `grep -l "^[^#-]" specification/*.md` → Verify not all lines are paragraphs
      4. Check each doc for required sections per plan
    Expected Result: 100% compliance
    Evidence: .sisyphus/evidence/f1-compliance-report.md
  ```

  **Evidence to Capture**:
  - [ ] Compliance report: f1-compliance-report.md

  **Output**: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [x] F2. **Consistency Check** — `unspecified-high`

  **What to do**:
  - Read all specification documents
  - Verify: every term used is defined in glossary
  - Verify: every mechanic referenced has a home document
  - Verify: numbers/formulas are consistent across docs
  - Verify: no contradictions between docs
  - Flag any inconsistency with file:line reference

  **Acceptance Criteria**:
  - [ ] All terms in glossary
  - [ ] All mechanics have home documents
  - [ ] Formulas consistent (treasury, reward, etc.)
  - [ ] Zero contradictions found

  **QA Scenarios**:

  ```
  Scenario: Cross-document consistency
    Tool: Bash (grep, diff)
    Preconditions: All docs exist
    Steps:
      1. Extract all capitalized terms from docs and verify in glossary
      2. Compare treasury formula in Economy vs Reward docs
      3. Compare voting rules in Rules vs Voting Protocol docs
      4. Compare event visibility in Event System vs Observation Space docs
    Expected Result: Zero inconsistencies
    Evidence: .sisyphus/evidence/f2-consistency-report.md
  ```

  **Evidence to Capture**:
  - [ ] Consistency report: f2-consistency-report.md

  **Output**: `Terms [N/N defined] | Mechanics [N/N documented] | Formulas [N/N consistent] | VERDICT`

- [x] F3. **Completeness Verification** — `unspecified-high`

  **What to do**:
  - Start from user requirements
  - For each requirement: locate the exact document and section that defines it
  - Verify no requirement is missing
  - Verify edge cases are covered (tie-breaking, abstention, zero treasury, all ministers abstain)
  - Save evidence to `.sisyphus/evidence/final-qa/`

  **Acceptance Criteria**:
  - [ ] All user requirements covered
  - [ ] Edge cases documented
  - [ ] No missing mechanics

  **QA Scenarios**:

  ```
  Scenario: Requirements coverage
    Tool: Bash (grep)
    Preconditions: All docs exist
    Steps:
      1. Search for "sequential voting" in docs
      2. Search for "event severity" in docs
      3. Search for "surplus rollover" in docs
      4. Search for "bankruptcy" in docs
      5. Search for "prosperity" or "GDP" in docs
      6. Search for "tie-breaking" in docs
      7. Search for "abstention" in docs
    Expected Result: All requirements found with specific definitions
    Evidence: .sisyphus/evidence/f3-completeness-report.md
  ```

  **Evidence to Capture**:
  - [ ] Completeness report: f3-completeness-report.md

  **Output**: `Requirements [N/N covered] | Edge Cases [N/N handled] | VERDICT`

---

## Commit Strategy

- **Wave 1**: `docs(spec): add game overview, rules, turn structure, glossary, guardrails`
- **Wave 2**: `docs(spec): add economy, voting, events, action space, observation, reward`
- **Wave 3**: `docs(spec): add success criteria, examples, index, final audit`
- **FINAL**: `docs(spec): complete specification document set`

---

## Success Criteria

### Verification Commands
```bash
# All spec files exist
ls specification/*.md | wc -l  # Expected: 14

# No "TBD" or "to be determined" in any spec
grep -ri "TBD\|to be determined\|TODO\|FIXME" specification/  # Expected: empty

# All docs use bullet points (not paragraph-only)
# Verified manually by agent reading samples from each file

# Cross-references resolve
# Verified by agent checking each referenced doc ID exists
```

### Final Checklist
- [ ] All "Must Have" present in spec documents
- [ ] All "Must NOT Have" absent from spec documents
- [ ] All 14 documents exist
- [ ] No "TBD" or ambiguous placeholders
- [ ] Consistent terminology across all docs
- [ ] Edge cases documented
- [ ] Two-reader test passed (equivalent interpretation)
