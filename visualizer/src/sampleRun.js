// sampleRun.js
// ----------------------------------------------------------------------------
// Synthetic episode used as a fallback when no real telemetry is loaded.
// Shape mirrors the planned `evaluation/export_episode.py` JSON output so the
// visualizer can render real training rollouts the moment that exporter exists.
// ----------------------------------------------------------------------------

const SECTORS = [
  { name: 'Social', full_name: 'Social/Municipal', baseline: 60 },
  { name: 'Agriculture', full_name: 'Agriculture', baseline: 70 },
  { name: 'Health', full_name: 'Health', baseline: 90 },
  { name: 'Education', full_name: 'Education/R&D', baseline: 80 },
  { name: 'Defense', full_name: 'Defense', baseline: 100 },
  { name: 'Commerce', full_name: 'Commerce', baseline: 75 },
];

const POP0 = 1_000_000;
const INITIAL_TREASURY = 1000;
const BASELINE_TAX = 100;
const PROD_BOUNDS = [0.5, 2.0];
const PROD_STEP = 0.05;

const NEG_EVENTS = [
  {
    id: 'war',
    name: 'War',
    severity_range: [3, 5],
    affected_sectors: { Defense: 2.5, Agriculture: 1.3, Commerce: 1.2 },
    category: 'moderate',
    narrative:
      'Enemy forces have crossed the border. Defense requests emergency funding for military operations.',
  },
  {
    id: 'famine',
    name: 'Famine',
    severity_range: [2, 4],
    affected_sectors: { Agriculture: 2.0, Health: 1.5, Commerce: 1.3 },
    category: 'moderate',
    narrative:
      'Harvest projections indicate a 40% shortfall. Agricultural imports required.',
  },
  {
    id: 'virus',
    name: 'Virus Outbreak',
    severity_range: [2, 5],
    affected_sectors: { Health: 2.5, Commerce: 1.4, Agriculture: 1.3 },
    category: 'moderate',
    narrative:
      'A viral outbreak has spread across multiple provinces. Health ministry requests emergency medical supplies.',
  },
  {
    id: 'unemployment',
    name: 'Unemployment Crisis',
    severity_range: [2, 4],
    affected_sectors: { Social: 2.0, Commerce: 1.5, Education: 1.2 },
    category: 'moderate',
    narrative:
      'Unemployment rates have spiked. Social services report increased benefit claims.',
  },
  {
    id: 'infrastructure_collapse',
    name: 'Infrastructure Collapse',
    severity_range: [3, 4],
    affected_sectors: { Social: 2.5, Commerce: 1.4, Defense: 1.2 },
    category: 'moderate',
    narrative:
      'A critical bridge has collapsed. Social services report transport disruptions.',
  },
];

const POS_EVENTS = [
  {
    id: 'trade_agreement',
    name: 'Trade Agreement',
    severity_range: [1, 2],
    affected_sectors: { Commerce: 0.9 },
    treasury_injection: 200,
    category: 'minor',
    narrative:
      'New trade agreement signed. Export revenues projected to increase.',
  },
  {
    id: 'agricultural_bounty',
    name: 'Agricultural Bounty',
    severity_range: [1, 2],
    affected_sectors: { Agriculture: 0.7 },
    treasury_injection: 180,
    category: 'minor',
    narrative:
      'Harvest projections exceed expectations. Agricultural sector reports record yields.',
  },
  {
    id: 'diplomatic_victory',
    name: 'Diplomatic Victory',
    severity_range: [1, 2],
    affected_sectors: { Defense: 0.8 },
    treasury_injection: 250,
    category: 'minor',
    narrative:
      'Diplomatic negotiations successful. Regional tensions declining.',
  },
];

// ── Tiny seeded RNG so the sample episode is deterministic ────────────────
function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const rand = mulberry32(42);

function randInt(lo, hi) {
  return Math.floor(rand() * (hi - lo + 1)) + lo;
}

function pick(arr) {
  return arr[Math.floor(rand() * arr.length)];
}

function severityMultiplier(severity, isPositive) {
  // Severity → multiplier sample (matches spec table)
  const ranges = isPositive
    ? { 1: [0.95, 1.0], 2: [0.85, 0.95] }
    : { 1: [1.0, 1.2], 2: [1.2, 1.5], 3: [1.5, 2.0], 4: [2.0, 3.0], 5: [3.0, 5.0] };
  const [lo, hi] = ranges[severity] || [1, 1];
  return lo + rand() * (hi - lo);
}

function rollEvents(roundNum) {
  // ~40% no event, 35% minor (positive often), 20% moderate negative, 4% critical, 1% compound
  const r = rand();
  if (r < 0.4) return [];
  if (r < 0.75) {
    // minor — pick a positive event most of the time
    const tmpl = rand() < 0.7 ? pick(POS_EVENTS) : pick(NEG_EVENTS.filter(e => e.severity_range[0] <= 2));
    return [instantiate(tmpl, POS_EVENTS.includes(tmpl), roundNum)];
  }
  if (r < 0.95) return [instantiate(pick(NEG_EVENTS), false, roundNum)];
  if (r < 0.99) {
    const tmpl = pick(NEG_EVENTS.filter(e => e.severity_range[1] >= 4));
    return [instantiate(tmpl, false, roundNum, 5)];
  }
  // compound — two negative events
  return [instantiate(pick(NEG_EVENTS), false, roundNum, 5), instantiate(pick(NEG_EVENTS), false, roundNum, 4)];
}

function instantiate(tmpl, isPositive, roundNum, forcedSeverity = null) {
  const [lo, hi] = tmpl.severity_range;
  const severity = forcedSeverity ?? randInt(lo, hi);
  const intensity = severityMultiplier(severity, isPositive);
  const affected = {};
  for (const [k, v] of Object.entries(tmpl.affected_sectors)) {
    // Scale the catalog multiplier by severity intensity factor
    if (isPositive) {
      affected[k] = Math.max(0.5, v * (1 - (severity - 1) * 0.05));
    } else {
      affected[k] = +(v * (intensity / 2)).toFixed(2);
      // keep at least the base catalog mult
      affected[k] = Math.max(affected[k], v);
    }
  }
  return {
    round: roundNum,
    id: tmpl.id,
    name: tmpl.name,
    severity,
    affected_sectors: affected,
    category: tmpl.category,
    narrative: tmpl.narrative,
    treasury_injection: tmpl.treasury_injection || 0,
    is_positive: isPositive,
  };
}

// ── Reward & revenue helpers (mirror spec 04 + 09) ────────────────────────
function thresholds(baseline, population, eventMult) {
  const demand = baseline * (population / POP0) * eventMult;
  return {
    demand,
    critical: demand * 0.4,
    surplus: demand * 1.5,
    wastage: demand * 2.5,
  };
}

function revenueFactor(x, t) {
  if (x < t.critical) return null;
  if (x < t.demand) return (x - t.critical) / (t.demand - t.critical);
  if (x <= t.surplus) {
    const u = (x - t.demand) / (t.surplus - t.demand);
    return 1.0 + 0.8 * u;
  }
  const k = Math.log(1.8) / (t.wastage - t.surplus);
  return 1.8 * Math.exp(-k * (x - t.surplus));
}

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

// ── Synthetic agent debate / proposal lines ────────────────────────────────
const DEBATE_LINES = {
  Social: [
    'Municipal services are stretched thin; we need to maintain a stable allocation.',
    'Public satisfaction is dropping. A modest bump would steady morale.',
    'Holding the line — we don’t need more this round.',
  ],
  Agriculture: [
    'Yields are below projection. We must lock in food security.',
    'Bounty conditions — request can be lower this quarter.',
    'Supply chains exposed; recommend a buffer above demand.',
  ],
  Health: [
    'Outbreak indicators are rising. We need to over-fund health now.',
    'Capacity is healthy. A baseline allocation is sufficient.',
    'Recommend a profit-zone allocation to shore up reserves.',
  ],
  Education: [
    'R&D pipeline is strong; modest sustaining investment is enough.',
    'Innovation grant is paying back — keep close to demand.',
    'Need to absorb teacher shortage costs this quarter.',
  ],
  Defense: [
    'Border tensions are escalating. We must allocate above demand.',
    'Diplomacy is buying us time. Demand is sufficient.',
    'Sustaining mobilization requires a buffer.',
  ],
  Commerce: [
    'Trade pipeline is healthy. We can stay close to demand.',
    'Market signal is volatile. A small buffer is prudent.',
    'Reduced import costs; lower allocation acceptable.',
  ],
};

const VOTES = ['YES', 'NO', 'ABSTAIN'];

function pickVote(p, isOwn) {
  if (isOwn) return 'ABSTAIN';
  // 70% YES, 15% NO, 15% ABSTAIN — soft tilt toward consensus
  if (p < 0.7) return 'YES';
  if (p < 0.85) return 'NO';
  return 'ABSTAIN';
}

function justification(dept, target, demand) {
  const ratio = (target / demand).toFixed(2);
  if (target / demand < 0.95) {
    return `${dept}: requesting ${ratio}× demand to free treasury for higher-priority sectors.`;
  }
  if (target / demand > 1.4) {
    return `${dept}: pushing into the profit zone (${ratio}× demand) to capture revenue factor near 1.8.`;
  }
  return `${dept}: targeting ${ratio}× demand — within profit zone, away from wastage.`;
}

// ── Build the episode ─────────────────────────────────────────────────────
export function buildSampleEpisode() {
  const rounds = [];
  let treasury = INITIAL_TREASURY;
  let productivity = 1.0;
  let population = POP0;
  let cumReward = 0;
  let prosperityStreak = 0;
  let shutdownCounter = 0;

  const eventLedger = [];
  const policyName = 'OptimalZone (1.3× demand) — synthetic';

  for (let r = 1; r <= 50; r += 1) {
    const events = rollEvents(r);
    eventLedger.push(...events);

    // Aggregate event multipliers per sector
    const eventMult = Object.fromEntries(SECTORS.map(s => [s.name, 1]));
    let crisisOccurred = false;
    let treasuryInjection = 0;
    for (const e of events) {
      for (const [s, m] of Object.entries(e.affected_sectors)) {
        eventMult[s] = (eventMult[s] || 1) * m;
      }
      if (e.severity >= 4) crisisOccurred = true;
      treasuryInjection += e.treasury_injection || 0;
    }
    treasury += treasuryInjection;

    // Compute thresholds for this round
    const sectorThresholds = {};
    for (const s of SECTORS) {
      sectorThresholds[s.name] = thresholds(s.baseline, population, eventMult[s.name]);
    }

    // ── Synthetic debate (one line per minister, ~70% chance to speak) ─
    const debate = SECTORS.filter(() => rand() < 0.72).map(s => ({
      agent_id: `minister_${s.name.toLowerCase()}`,
      department: s.name,
      message: pick(DEBATE_LINES[s.name]),
    }));

    // ── Proposals (rotating order) ────────────────────────────────────
    const startIdx = (r - 1) % SECTORS.length;
    const order = [
      ...SECTORS.slice(startIdx),
      ...SECTORS.slice(0, startIdx),
    ];

    const proposals = [];
    let runningTreasury = treasury;
    for (const s of order) {
      const t = sectorThresholds[s.name];
      // Optimal-zone-ish target with noise
      let target = t.demand * (1.25 + (rand() - 0.5) * 0.25);
      // Crisis-aware bump for affected sectors
      if (eventMult[s.name] > 1.5) target = t.demand * 1.35;
      if (eventMult[s.name] < 0.95) target = t.demand * 1.05;
      target = Math.max(0, Math.min(target, runningTreasury));
      // Occasionally a bad agent over-shoots into wastage
      if (rand() < 0.04) target = Math.min(t.wastage * 1.05, runningTreasury);
      // Occasionally an agent under-funds (still above critical)
      if (rand() < 0.03) target = t.critical * 1.05;
      const amount = Math.round(target);

      const proposalId = `r${r}_${s.name}`;
      proposals.push({
        proposal_id: proposalId,
        agent_id: `minister_${s.name.toLowerCase()}`,
        department: s.name,
        amount,
        justification: justification(s.name, amount, t.demand),
        timestamp_phase: 3,
      });
    }

    // ── Voting ────────────────────────────────────────────────────────
    const votes = [];
    const voteResults = [];
    const approvedAlloc = {};
    for (const p of proposals) {
      const proposalVotes = [];
      let yes = 0;
      let no = 0;
      let abstain = 0;
      for (const s of SECTORS) {
        const isOwn = s.name === p.department;
        const vote = pickVote(rand(), isOwn);
        proposalVotes.push({
          proposal_id: p.proposal_id,
          agent_id: `minister_${s.name.toLowerCase()}`,
          department: s.name,
          vote,
        });
        if (vote === 'YES') yes += 1;
        else if (vote === 'NO') no += 1;
        else abstain += 1;
      }
      votes.push(...proposalVotes);
      const status = yes > no ? 'APPROVED' : 'REJECTED';
      voteResults.push({
        proposal_id: p.proposal_id,
        department: p.department,
        amount: p.amount,
        yes,
        no,
        abstain,
        status,
      });
      if (status === 'APPROVED' && approvedAlloc[p.department] === undefined) {
        // Sequential treasury depletion check
        const sumSoFar = Object.values(approvedAlloc).reduce((a, b) => a + b, 0);
        if (sumSoFar + p.amount <= treasury) {
          approvedAlloc[p.department] = p.amount;
        } else {
          // auto-reject due to treasury exhaustion
          voteResults[voteResults.length - 1].status = 'AUTO_REJECTED_INSUFFICIENT_TREASURY';
        }
      }
    }

    // Final allocations dict (zero for rejected)
    const allocations = Object.fromEntries(
      SECTORS.map(s => [s.name, approvedAlloc[s.name] || 0]),
    );
    const totalAlloc = Object.values(allocations).reduce((a, b) => a + b, 0);

    // ── Critical threshold check ──────────────────────────────────────
    let criticalFailed = false;
    let failedSector = null;
    for (const s of SECTORS) {
      if (allocations[s.name] < sectorThresholds[s.name].critical && allocations[s.name] >= 0) {
        criticalFailed = true;
        failedSector = s.name;
        break;
      }
    }

    // ── Revenue + treasury update ─────────────────────────────────────
    let totalRevenue = 0;
    let surplusReturned = 0;
    const revenues = {};
    const consumptions = {};
    const revenueFactors = {};
    let underAllocCount = 0;
    let overAllocCount = 0;

    for (const s of SECTORS) {
      const a = allocations[s.name];
      const t = sectorThresholds[s.name];
      revenueFactors[s.name] = 0;
      revenues[s.name] = 0;
      consumptions[s.name] = 0;
      if (criticalFailed) continue;
      const rf = revenueFactor(a, t);
      if (rf === null) {
        revenues[s.name] = 0;
        revenueFactors[s.name] = 0;
        continue;
      }
      revenueFactors[s.name] = rf;
      revenues[s.name] = a * rf * productivity;
      consumptions[s.name] = Math.min(a, t.demand);
      totalRevenue += revenues[s.name];
      surplusReturned += a - consumptions[s.name];
      if (a > t.surplus) overAllocCount += 1;
      else if (a < t.demand && a >= t.critical) underAllocCount += 1;
    }

    const treasuryBefore = treasury;
    if (!criticalFailed) {
      treasury = treasury - totalAlloc + totalRevenue + surplusReturned + BASELINE_TAX;
    }
    const treasuryAfter = treasury;

    // ── Productivity / population update ─────────────────────────────
    const rfList = SECTORS.map(s => revenueFactors[s.name]);
    const avgRf = rfList.reduce((a, b) => a + b, 0) / rfList.length;
    if (!criticalFailed) {
      productivity = clamp(
        productivity + PROD_STEP * (avgRf - 1.0),
        PROD_BOUNDS[0],
        PROD_BOUNDS[1],
      );
      const birth = 0.005 * productivity;
      const death = 0.002 + (crisisOccurred ? 0.01 : 0);
      population = Math.round(population * (1 + birth - death));
    }

    // ── Reward ───────────────────────────────────────────────────────
    const baseReward = totalRevenue / Math.max(population, 1);
    const productivityBonus = 50 * (productivity - 1.0);
    const survivalBonus = 10 * r;
    const overPenalty = -5 * overAllocCount;
    const underPenalty = -10 * underAllocCount;
    const criticalPenalty = criticalFailed ? -1000 : 0;
    const totalReward = baseReward + productivityBonus + survivalBonus + overPenalty + underPenalty + criticalPenalty;
    cumReward += totalReward;

    // ── Termination ──────────────────────────────────────────────────
    let done = false;
    let terminationReason = null;
    if (criticalFailed) {
      done = true;
      terminationReason = `CRITICAL_FAILURE (${failedSector} below 40% of demand)`;
    } else if (treasury <= 0) {
      done = true;
      terminationReason = 'BANKRUPTCY';
    } else if (totalAlloc === 0) {
      shutdownCounter += 1;
      if (shutdownCounter >= 2) {
        done = true;
        terminationReason = 'SHUTDOWN';
      }
    } else {
      shutdownCounter = 0;
    }

    const prosperity = totalRevenue / Math.max(population, 1);
    if (!done && prosperity >= 0.0015) {
      prosperityStreak += 1;
      if (prosperityStreak >= 5) {
        done = true;
        terminationReason = 'PROSPERITY_ACHIEVED';
      }
    } else {
      prosperityStreak = 0;
    }
    if (!done && r === 50) {
      done = true;
      terminationReason = 'MAX_ROUNDS';
    }

    rounds.push({
      round_num: r,
      year: Math.floor((r - 1) / 4) + 1,
      quarter: ((r - 1) % 4) + 1,
      events,
      crisis_occurred: crisisOccurred,
      treasury_injection: treasuryInjection,
      debate,
      proposal_order: order.map(s => s.name),
      proposals,
      votes,
      vote_results: voteResults,
      allocations,
      consumptions,
      revenues,
      revenue_factors: revenueFactors,
      thresholds: sectorThresholds,
      event_multipliers: eventMult,
      treasury_before: +treasuryBefore.toFixed(2),
      treasury_after: +treasuryAfter.toFixed(2),
      total_allocation: totalAlloc,
      total_revenue: +totalRevenue.toFixed(2),
      surplus_returned: +surplusReturned.toFixed(2),
      population,
      productivity: +productivity.toFixed(4),
      avg_revenue_factor: +avgRf.toFixed(4),
      prosperity: +prosperity.toFixed(6),
      reward: {
        base_reward: +baseReward.toFixed(6),
        productivity_bonus: +productivityBonus.toFixed(4),
        survival_bonus: +survivalBonus.toFixed(4),
        over_alloc_penalty: overPenalty,
        under_alloc_penalty: underPenalty,
        critical_penalty: criticalPenalty,
        total: +totalReward.toFixed(4),
      },
      cumulative_reward: +cumReward.toFixed(4),
      done,
      termination_reason: terminationReason,
    });

    if (done) break;
  }

  const last = rounds[rounds.length - 1];
  // Per spec 04: final prosperity = (Treasury + sum(Revenue)) / Population.
  // This differs from the per-round prosperity reading (revenue/population only)
  // and matters for terminal rounds where treasury may carry significant value.
  const finalProsperity =
    (last.treasury_after + last.total_revenue) / Math.max(last.population, 1);
  return {
    episode_id: 'sample-001',
    seed: 42,
    policy: policyName,
    config: {
      sectors: SECTORS,
      pop_0: POP0,
      initial_treasury: INITIAL_TREASURY,
      baseline_tax: BASELINE_TAX,
      productivity_bounds: PROD_BOUNDS,
      max_rounds: 50,
    },
    rounds,
    summary: {
      rounds_survived: last.round_num,
      total_reward: +cumReward.toFixed(4),
      final_treasury: last.treasury_after,
      final_prosperity: +finalProsperity.toFixed(6),
      final_productivity: last.productivity,
      final_population: last.population,
      termination_reason: last.termination_reason,
    },
  };
}

export const sampleEpisode = buildSampleEpisode();
