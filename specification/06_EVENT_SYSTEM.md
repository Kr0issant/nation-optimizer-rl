# 06 — Event System

Event generation, catalog, severity mechanics, and observability rules.

---

## Event Generation Rules

- Events are generated at the start of each round (Phase 1 of Turn Structure)
- **Maximum 2 events per round** — enforced by Guardrails
- **Event count distribution** (mostly normal, black swan crises):
  - 40% chance: 0 events (normal government function, no disruption)
  - 35% chance: 1 minor/positive event (mundane government operations)
  - 20% chance: 1 moderate/major event (significant challenge)
  - 4% chance: 1 critical event (crisis requiring response)
  - 1% chance: 2+ events (compound crisis, multiple challenges)
- Events are drawn from a weighted catalog based on department relevancy
- Each event is assigned a severity level (1–5) at generation time
- Each event affects one or more departments (tagged at generation)
- **Most rounds are normal government operations. Black swan crises are rare but devastating.**

---

## Severity Levels

| Level | Name | Meaning |
|-------|------|---------|
| 1 | Minimal | Barely noticeable impact on operations |
| 2 | Minor | Slight disruption, manageable with existing resources |
| 3 | Moderate | Significant strain, requires strategic response |
| 4 | Major | Critical disruption, may cause budget reallocation |
| 5 | Critical | Existential threat, immediate action required |

- Severity is assigned per-event and is fully visible to all agents
- Severity determines the cost multiplier: `Severity_Multiplier = severity * 10`

---

## Event Cost Formula

- `Event_Cost = Base_Cost * Severity_Multiplier * Random_Variance`
- `Severity_Multiplier` = severity × 10 (e.g., severity 3 → multiplier 30)
- `Random_Variance` = uniform random draw in range [0.8, 1.2]
- `Base_Cost` is event-specific (defined per event type in catalog)
- Exact cost is **hidden** from agents until round resolution
- Agents see narrative + severity; they do NOT see Base_Cost, multiplier, or variance

---

## What Agents Observe

- **Event name** — e.g., "War", "Famine", "Medical Breakthrough"
- **Narrative description** — contextual text describing the event
- **Severity level** — numeric scale 1–5, fully visible
- **Affected department(s)** — which department(s) the event impacts
- Agents MAY infer approximate cost impact from severity and narrative
- Agents do NOT receive cost probability distributions or inference hints

---

## What Is Hidden

- **Exact cost impact** — currency value is not revealed until after round resolves
- **Base_Cost** — event-specific cost baseline is not disclosed
- **Severity_Multiplier** — formula is not provided to agents
- **Random_Variance** — the 0.8–1.2 factor is not disclosed
- These hidden values are fixed once the event is generated for the round

---

## Department Relevancy Mapping

| Department | High-Relevance Events | Low-Relevance Events |
|------------|---------------------|---------------------|
| Defense | War, Military Conflict, Border Skirmish | Famine, Virus Outbreak |
| Agriculture | Famine, Crop Failure, Drought | Military Conflict, Economic Boom |
| Health | Virus Outbreak, Medical Breakthrough, Epidemic | Infrastructure Collapse |
| Infrastructure | Infrastructure Collapse, Blackout, Transport Failure | Famine, Economic Boom |
| Education | Brain Drain, Education Reform, Budget Crisis | War, Infrastructure Collapse |
| Economy | Economic Boom, Recession, Market Crash | Education Reform, Border Skirmish |

- Events can affect multiple departments simultaneously
- An event tagged to a department impacts that department's revenue or costs
- All departments observe all events regardless of relevancy

---

## Event Catalog

### Negative Events

#### War
- **Affected departments**: Defense (primary), Agriculture, Infrastructure
- **Base_Cost**: 150
- **Severity range**: 3–5
- **Description**: Armed conflict depletes resources, diverts budget, and disrupts supply chains
- **Narrative example**: "Enemy forces have crossed the border. Defense requests emergency funding for military operations. Agricultural and infrastructure sectors report supply chain disruptions."

---

#### Famine
- **Affected departments**: Agriculture (primary), Health, Economy
- **Base_Cost**: 100
- **Severity range**: 2–4
- **Description**: Crop failure and food shortage strain health services and reduce workforce productivity
- **Narrative example**: "Harvest projections indicate a 40% shortfall. Agricultural imports required. Health services report increased malnutrition cases. Workforce productivity declining."

---

#### Virus Outbreak
- **Affected departments**: Health (primary), Economy, Agriculture
- **Base_Cost**: 120
- **Severity range**: 2–5
- **Description**: Epidemic demands emergency health spending and reduces labor availability
- **Narrative example**: "A viral outbreak has spread across multiple provinces. Health ministry requests emergency medical supplies. Economic output declining as workforce falls ill. Food distribution affected."

---

#### Infrastructure Collapse
- **Affected departments**: Infrastructure (primary), Economy, Defense
- **Base_Cost**: 130
- **Severity range**: 3–4
- **Description**: Critical infrastructure failure disrupts transport, communication, and economic activity
- **Narrative example**: "A critical bridge has collapsed. Infrastructure repairs required urgently. Economic activity slowed. Defense logistics affected."

---

#### Education Reform
- **Affected departments**: Education
- **Base_Cost**: 80
- **Severity range**: 2–3
- **Description**: Education policy changes require budget reallocation
- **Narrative example**: "New education standards require teacher training and curriculum updates. Budget reallocation necessary. Long-term productivity gains expected."

---

#### Budget Crisis
- **Affected departments**: Economy (primary), Education, Infrastructure
- **Base_Cost**: 90
- **Severity range**: 2–3
- **Description**: Unexpected deficit requires cutting allocations across departments
- **Narrative example**: "Treasury audit reveals unexpected shortfall. Across-department cuts required. Infrastructure maintenance deferred. Education programs scaled back."

---

### Positive Events

#### Trade Agreement
- **Affected departments**: Commerce (primary)
- **Base_Cost**: -40 (negative = revenue gain)
- **Severity range**: 1–2
- **Description**: Favorable trade terms increase commerce revenue and economic activity
- **Narrative example**: "New trade agreement signed. Export revenues projected to increase. Commerce ministry reports favorable terms."

---

#### Technological Innovation
- **Affected departments**: Education (primary), Commerce
- **Base_Cost**: -30 (negative = revenue gain)
- **Severity range**: 1–2
- **Description**: R&D breakthrough improves productivity across sectors
- **Narrative example**: "Researchers have developed new efficiency technology. Education sector reports productivity gains. Long-term economic benefits projected."

---

#### Agricultural Bounty
- **Affected departments**: Agriculture (primary)
- **Base_Cost**: -35 (negative = revenue gain)
- **Severity range**: 1–2
- **Description**: Favorable weather and yields increase agricultural output
- **Narrative example**: "Harvest projections exceed expectations. Agricultural sector reports record yields. Food exports projected to increase."

---

#### Public Health Campaign Success
- **Affected departments**: Health (primary)
- **Base_Cost**: -20 (negative = cost reduction)
- **Severity range**: 1–2
- **Description**: Successful health initiatives reduce disease burden and costs
- **Narrative example**: "Public health campaign shows remarkable results. Disease incidence declining. Healthcare costs projected to decrease."

---

#### Infrastructure Upgrade
- **Affected departments**: Social (primary)
- **Base_Cost**: -15 (negative = cost reduction)
- **Severity range**: 1–2
- **Description**: New infrastructure reduces maintenance costs and improves services
- **Narrative example**: "New infrastructure project completed ahead of schedule. Social services report improved efficiency. Maintenance costs declining."

---

#### Diplomatic Victory
- **Affected departments**: Defense (primary)
- **Base_Cost**: -25 (negative = cost reduction)
- **Severity range**: 1–2
- **Description**: Successful diplomacy reduces defense spending requirements
- **Narrative example**: "Diplomatic negotiations successful. Regional tensions declining. Defense spending requirements reduced."

---

### Black Swan Events (Rare, Extreme)

#### Financial Collapse
- **Affected departments**: All departments (systemic)
- **Base_Cost**: 200
- **Severity range**: 5 (always critical)
- **Chance**: 0.5% (very rare)
- **Description**: Systemic financial crisis impacts all sectors simultaneously
- **Narrative example**: "Financial markets have collapsed. All sectors report severe disruption. Emergency measures required to prevent complete economic breakdown."

---

#### Natural Disaster
- **Affected departments**: Random department (primary), all others (secondary)
- **Base_Cost**: 180
- **Severity range**: 5 (always critical)
- **Chance**: 1% (rare)
- **Description**: Major natural catastrophe disrupts normal government operations
- **Narrative example**: "Major earthquake has struck. Infrastructure crippled. Emergency response required across all departments."

---

#### Pandemic
- **Affected departments**: Health (primary), all others (secondary)
- **Base_Cost**: 150
- **Severity range**: 5 (always critical)
- **Chance**: 0.5% (very rare)
- **Description**: Global health emergency requires full government response
- **Narrative example**: "Pandemic declared. Healthcare system overwhelmed. All departments must redirect resources to emergency response."

---

## Event Ledger

- The Event Ledger records all events that have occurred in the current episode
- Past events are fully visible to all agents (name, narrative, severity, cost impact after resolution)
- Agents can observe past event patterns to inform future predictions
- Future events are not disclosed; only events that have occurred are visible
- The ledger is append-only per episode; it does not carry over between episodes

---

## Positive vs Negative Events

- **Negative events** increase costs (War, Famine, Virus Outbreak, Infrastructure Collapse, Education Reform, Budget Crisis)
  - Base_Cost is positive; cost is deducted from treasury
- **Positive events** reduce costs or generate revenue (Trade Agreement, Tech Innovation, Agricultural Bounty, Health Campaign, Infrastructure Upgrade, Diplomatic Victory)
  - Base_Cost is negative; cost is a credit to treasury
- **Black Swan events** are rare but devastating (Financial Collapse, Natural Disaster, Pandemic)
  - Always severity 5; impact all departments
  - Occur with very low probability but require crisis management
- Positive and negative events follow the same visibility rules
- Severity applies to all events (higher severity = larger magnitude)