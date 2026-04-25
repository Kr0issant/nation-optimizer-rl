# 06 — Event System

Event generation, catalog, severity mechanics, and observability rules.

---

## Design Philosophy: Multiplicative Demand Scaling

The old event system used additive costs: `Event_Cost = Base_Cost × Severity × Variance`. This approach fails at scale. A +50 cost is trivial when baseline is 1000 but devastating when baseline is 60.

The new system uses **multiplicative demand scaling**:

```
Demand_d = Baseline_d × (Population_t / Pop₀) × Event_Multiplier
```

This ensures events are proportionally impactful regardless of sector size. A war that doubles defense demand hits just as hard whether baseline is 100 or 1000.

**Positive events** inject cash into treasury rather than reducing costs. This models real government revenue (taxes, tariffs, aid) rather than negative expenses.

---

## Event Generation Rules

- Events are generated at the start of each round (Phase 1 of Turn Structure)
- **Maximum 2 events per round** — enforced by Guardrails
- **Event count distribution** (mostly normal, black swan crises):
  - 40% chance: 0 events (normal government function, no disruption)
  - 35% chance: 1 minor event (positive or small negative)
  - 20% chance: 1 moderate/major event (significant challenge)
  - 4% chance: 1 critical event (crisis requiring response)
  - 1% chance: 2+ events (compound crisis, multiple challenges)
- Events are drawn from a weighted catalog based on department relevancy
- Each event is assigned a severity level (1–5) at generation time
- Each event affects one or more departments (tagged at generation)
- **Most rounds are normal government operations. Black swan crises are rare but devastating.**

---

## Severity Levels

| Level | Name | Multiplier Range | Example |
|-------|------|-----------------|---------|
| 1 | Minimal | ×1.0 – ×1.2 | Minor policy change |
| 2 | Minor | ×1.2 – ×1.5 | Local disruption |
| 3 | Moderate | ×1.5 – ×2.0 | Regional crisis |
| 4 | Major | ×2.0 – ×3.0 | National emergency |
| 5 | Critical/Black Swan | ×3.0 – ×5.0 | Existential threat |

- Severity is assigned per-event and is fully visible to all agents
- Severity determines the Event_Multiplier range applied to department demand
- Exact multiplier within the range is **hidden** from agents until round resolution

---

## Event Impact Formula

For each department d affected by an event:

```
Demand_d = Baseline_d × (Population_t / Pop₀) × Event_Multiplier
```

Where:
- `Baseline_d` — department's baseline demand (Social: 60, Agriculture: 70, Health: 90, Education: 80, Defense: 100, Commerce: 75)
- `Population_t / Pop₀` — population growth factor (population at time t divided by initial population)
- `Event_Multiplier` — severity-derived multiplier (see Severity Levels table)

For **negative events**, the multiplier is greater than 1.0, increasing demand.

For **positive events**, the multiplier is less than 1.0 (reducing demand), AND the event injects cash into the treasury.

---

## What Agents Observe

- **Event name** — e.g., "War", "Famine", "Medical Breakthrough"
- **Narrative description** — contextual text describing the event
- **Severity level** — numeric scale 1–5, fully visible
- **Affected department(s)** — which department(s) the event impacts
- Agents MAY infer approximate demand impact from severity and narrative
- Agents do NOT receive exact multiplier values or treasury injection amounts

---

## What Is Hidden

- **Exact Event_Multiplier** — the specific multiplier value is not disclosed
- **Treasury injection amount** — cash amount from positive events is not disclosed
- **Random variance within severity range** — the exact multiplier draw is not disclosed
- These hidden values are fixed once the event is generated for the round

---

## Department Relevancy Mapping

v1 Departments: Social/Municipal, Agriculture, Health, Education/R&D, Defense, Commerce

| Department | High-Relevance Events | Low-Relevance Events |
|------------|---------------------|---------------------|
| Defense | War, Military Conflict, Border Skirmish, Diplomatic Victory | Famine, Virus Outbreak |
| Agriculture | Famine, Crop Failure, Drought, Contamination, Agricultural Bounty | Military Conflict, Economic Boom |
| Health | Virus Outbreak, Epidemic, Contamination, Public Health Campaign | Infrastructure Collapse |
| Education | Brain Drain, Education Reform, Budget Crisis, Teacher Shortage, Technological Innovation | War, Infrastructure Collapse |
| Social/Municipal | Infrastructure Collapse, Blackout, Transport Failure, Unemployment, Public Distrust | Famine, Economic Boom |
| Commerce | Economic Boom, Recession, Market Crash, Trade Agreement, Unemployment | Education Reform, Border Skirmish |

- Events can affect multiple departments simultaneously
- An event tagged to a department impacts that department's demand
- All departments observe all events regardless of relevancy

---

## Event Catalog

### Negative Events (Increase Demand)

#### War
- **Affected departments**: Defense (primary), Agriculture, Commerce
- **Multiplier**: Defense ×2.5, Agriculture ×1.3, Commerce ×1.2
- **Severity range**: 3–5
- **Description**: Armed conflict depletes resources, diverts budget, and disrupts supply chains
- **Narrative example**: "Enemy forces have crossed the border. Defense requests emergency funding for military operations. Agricultural and commerce sectors report supply chain disruptions."

---

#### Famine
- **Affected departments**: Agriculture (primary), Health, Commerce
- **Multiplier**: Agriculture ×2.0, Health ×1.5, Commerce ×1.3
- **Severity range**: 2–4
- **Description**: Crop failure and food shortage strain health services and reduce workforce productivity
- **Narrative example**: "Harvest projections indicate a 40% shortfall. Agricultural imports required. Health services report increased malnutrition cases. Workforce productivity declining."

---

#### Virus Outbreak
- **Affected departments**: Health (primary), Commerce, Agriculture
- **Multiplier**: Health ×2.5, Commerce ×1.4, Agriculture ×1.3
- **Severity range**: 2–5
- **Description**: Epidemic demands emergency health spending and reduces labor availability
- **Narrative example**: "A viral outbreak has spread across multiple provinces. Health ministry requests emergency medical supplies. Economic output declining as workforce falls ill. Food distribution affected."

---

#### Unemployment
- **Affected departments**: Social (primary), Commerce, Education
- **Multiplier**: Social ×2.0, Commerce ×1.5, Education ×1.2
- **Severity range**: 2–4
- **Description**: Rising unemployment strains social services, reduces commerce tax revenue, and的压力 pressures education funding
- **Narrative example**: "Unemployment rates have spiked. Social services report increased benefit claims. Commerce ministry reports declining tax revenue. Education budgets under pressure as workforce development programs expand."

---

#### Teacher Shortage
- **Affected departments**: Education (primary), Social
- **Multiplier**: Education ×2.0, Social ×1.3
- **Severity range**: 2–4
- **Description**: Critical shortage of qualified teachers disrupts education delivery and strains social services
- **Narrative example**: "Schools report acute teacher shortages. Education ministry requests emergency hiring budget. Social services note increased youth counseling demand. Teacher training programs need investment."

---

#### Market Crash
- **Affected departments**: Commerce (primary), All others (secondary)
- **Multiplier**: Commerce ×2.5, All others ×1.2
- **Severity range**: 3–5
- **Description**: Financial markets collapse, reducing commerce revenue and straining all government functions
- **Narrative example**: "Stock markets have crashed. Commerce ministry reports severe revenue shortfall. All departments report reduced tax collections. Emergency measures required to maintain basic services."

---

#### Contamination
- **Affected departments**: Agriculture (primary), Health, Social
- **Multiplier**: Agriculture ×2.0, Health ×1.8, Social ×1.3
- **Severity range**: 2–4
- **Description**: Environmental contamination affects food supply and public health
- **Narrative example**: "Water supply contamination detected. Agricultural land affected. Health services report increased illness cases. Social services preparing for community relocation if spread continues."

---

#### Infrastructure Collapse
- **Affected departments**: Social (primary), Commerce, Defense
- **Multiplier**: Social ×2.5, Commerce ×1.4, Defense ×1.2
- **Severity range**: 3–4
- **Description**: Critical infrastructure failure disrupts transport, communication, and economic activity
- **Narrative example**: "A critical bridge has collapsed. Social services report transport disruptions. Commerce activity slowed. Defense logistics affected as supply routes are compromised."

---

#### Public Distrust
- **Affected departments**: Social (primary), All others (secondary)
- **Multiplier**: Social ×2.0, All others ×1.1
- **Severity range**: 2–4
- **Description**: Erosion of public confidence in government strains social cohesion and reduces compliance
- **Narrative example**: "Public trust in government institutions has declined significantly. Social services report increased resistance to public programs. All departments note reduced voluntary compliance. Recovery requires sustained transparency."

---

### Positive Events (Inject Treasury Cash)

Positive events reduce sector demand AND inject cash into treasury. The treasury injection is hidden from agents.

#### Trade Agreement
- **Affected departments**: Commerce (primary)
- **Multiplier**: Commerce demand ×0.9
- **Treasury injection**: +200
- **Severity range**: 1–2
- **Description**: Favorable trade terms increase commerce revenue and economic activity
- **Narrative example**: "New trade agreement signed. Export revenues projected to increase. Commerce ministry reports favorable terms. Treasury expected to receive tariff payments."

---

#### Technological Innovation
- **Affected departments**: Education (primary), Commerce
- **Multiplier**: Education demand ×0.8
- **Treasury injection**: +150
- **Severity range**: 1–2
- **Description**: R&D breakthrough improves productivity across sectors
- **Narrative example**: "Researchers have developed new efficiency technology. Education sector reports productivity gains. Long-term economic benefits projected. Patents and licensing expected to generate treasury revenue."

---

#### Agricultural Bounty
- **Affected departments**: Agriculture (primary)
- **Multiplier**: Agriculture demand ×0.7
- **Treasury injection**: +180
- **Severity range**: 1–2
- **Description**: Favorable weather and yields increase agricultural output and exports
- **Narrative example**: "Harvest projections exceed expectations. Agricultural sector reports record yields. Food exports projected to increase. Treasury to receive export tariffs."

---

#### Public Health Campaign
- **Affected departments**: Health (primary)
- **Multiplier**: Health demand ×0.8
- **Treasury injection**: +120
- **Severity range**: 1–2
- **Description**: Successful health initiatives reduce disease burden and future costs
- **Narrative example**: "Public health campaign shows remarkable results. Disease incidence declining. Healthcare costs projected to decrease. Treasury saves on future health emergency response."

---

#### Infrastructure Upgrade
- **Affected departments**: Social (primary)
- **Multiplier**: Social demand ×0.9
- **Treasury injection**: +100
- **Severity range**: 1–2
- **Description**: New infrastructure reduces maintenance costs and improves services
- **Narrative example**: "New infrastructure project completed ahead of schedule. Social services report improved efficiency. Maintenance costs declining. Treasury to receive infrastructure service fees."

---

#### Diplomatic Victory
- **Affected departments**: Defense (primary)
- **Multiplier**: Defense demand ×0.8
- **Treasury injection**: +250
- **Severity range**: 1–2
- **Description**: Successful diplomacy reduces defense spending requirements and may bring foreign aid
- **Narrative example**: "Diplomatic negotiations successful. Regional tensions declining. Defense spending requirements reduced. Allied nations providing economic assistance. Treasury to receive foreign aid payments."

---

#### High Public Enthusiasm
- **Affected departments**: All departments
- **Multiplier**: All demands ×0.9
- **Treasury injection**: +100
- **Severity range**: 1–2
- **Description**: Nationwide optimism boosts productivity and tax compliance
- **Narrative example**: "Citizen morale is at a record high. All sectors report improved productivity. Tax compliance increasing across all departments. Treasury expects higher than projected revenue."

---

### Black Swan Events (Rare, Extreme, Critical)

Black swan events are severity 5 and use the highest multiplier range (×3.0 – ×5.0). They are rare but devastating.

#### Natural Disaster
- **Affected departments**: Random department (primary), all others (secondary)
- **Multiplier**: Primary sector ×4.0, secondary sectors ×1.5
- **Severity**: Always 5
- **Description**: Major natural catastrophe disrupts normal government operations
- **Narrative example**: "A major earthquake has struck. One sector crippled with severe damage. Emergency response required across all departments. Recovery will require significant resource reallocation."

---

#### Compound Crisis
- **Affected departments**: Multiple departments simultaneously
- **Multiplier**: Each affected sector ×3.0 – ×4.0
- **Severity**: Always 5
- **Description**: Multiple crises strike simultaneously, overwhelming government capacity
- **Narrative example**: "Multiple crises have struck at once. All departments report critical demands. Government capacity severely strained. Emergency measures across all sectors required to prevent collapse."

---

## Event Ledger

- The Event Ledger records all events that have occurred in the current episode
- Past events are fully visible to all agents (name, narrative, severity, multiplier impact after resolution)
- Agents can observe past event patterns to inform future predictions
- Future events are not disclosed; only events that have occurred are visible
- The ledger is append-only per episode; it does not carry over between episodes

---

## Event Type Summary

| Type | Effect | Examples |
|------|--------|----------|
| **Negative** | Increase department demand via multiplier | War, Famine, Virus Outbreak, Unemployment, Market Crash |
| **Positive** | Reduce demand AND inject treasury cash | Trade Agreement, Agricultural Bounty, Diplomatic Victory, High Public Enthusiasm |
| **Black Swan** | Extreme multiplier across multiple sectors | Natural Disaster, Compound Crisis |

- Negative events: multiplier > 1.0, demand increases
- Positive events: multiplier < 1.0 (demand decreases) AND treasury receives cash injection
- Black swan events: multiplier ×3.0–×5.0, always severity 5
- All events follow the same visibility rules
- Severity applies to all events (higher severity = larger multiplier magnitude)

(End of file)
