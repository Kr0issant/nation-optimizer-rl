// normalizeEpisode.js
// ----------------------------------------------------------------------------
// Bridges two episode JSON shapes:
//
//   1. The synthetic shape produced by `src/sampleRun.js` (rich; includes
//      thresholds, event_multipliers, treasury_before/after, debate/votes…).
//
//   2. The lean shape that `core/game.py::StepResult.to_dict()` actually
//      emits today (single `treasury`, only `demands` per sector, no
//      orchestrator-level data, etc.).
//
// `normalizeEpisode()` returns a uniform shape that every visualizer
// component can rely on, deriving anything that's missing from the spec
// formulas in `specification/04_ECONOMY_MODEL.md`.
// ----------------------------------------------------------------------------

const CRITICAL_RATIO = 0.4;
const SURPLUS_RATIO = 1.5;
const WASTAGE_RATIO = 2.5;

function thresholdsFromDemand(demand) {
  return {
    critical: demand * CRITICAL_RATIO,
    demand,
    surplus: demand * SURPLUS_RATIO,
    wastage: demand * WASTAGE_RATIO,
  };
}

function aggregateEventMultipliers(events, sectorNames) {
  const out = Object.fromEntries(sectorNames.map(n => [n, 1]));
  for (const ev of events || []) {
    const aff = ev.affected_sectors || ev.affected_departments || {};
    if (Array.isArray(aff)) continue;
    for (const [name, mult] of Object.entries(aff)) {
      if (out[name] !== undefined) out[name] *= Number(mult) || 1;
    }
  }
  return out;
}

function deriveThresholds(round, sectorNames) {
  const existing = round.thresholds || {};
  const demands = round.demands || {};
  const out = {};
  for (const name of sectorNames) {
    if (existing[name] && existing[name].demand !== undefined) {
      const t = existing[name];
      out[name] = {
        critical: t.critical ?? t.demand * CRITICAL_RATIO,
        demand: t.demand,
        surplus: t.surplus ?? t.demand * SURPLUS_RATIO,
        wastage: t.wastage ?? t.demand * WASTAGE_RATIO,
      };
    } else if (demands[name] !== undefined) {
      out[name] = thresholdsFromDemand(Number(demands[name]) || 0);
    } else {
      out[name] = thresholdsFromDemand(0);
    }
  }
  return out;
}

function average(arr) {
  if (!arr.length) return 0;
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

function isPositiveEvent(ev) {
  if (typeof ev.is_positive === 'boolean') return ev.is_positive;
  if (Number(ev.treasury_injection) > 0) return true;
  if (typeof ev.category === 'string') return ev.category === 'positive';
  const aff = ev.affected_sectors || {};
  const mults = Object.values(aff).map(Number).filter(Number.isFinite);
  if (mults.length === 0) return false;
  return mults.every(m => m < 1);
}

function findFailingSectors(allocations, thresholds, sectorNames) {
  const failing = [];
  for (const name of sectorNames) {
    const a = Number(allocations[name] ?? 0);
    const t = thresholds[name] || {};
    if (a < (t.critical ?? Infinity)) failing.push(name);
  }
  return failing;
}

export function normalizeEpisode(raw) {
  if (!raw || !Array.isArray(raw.rounds)) return raw;

  const sectors = raw.config?.sectors || [];
  const sectorNames = sectors.map(s => s.name);

  let cum = 0;
  let prevTreasuryAfter = raw.config?.initial_treasury ?? 1000;

  const rounds = raw.rounds.map((r, i) => {
    const events = (r.events || []).map(ev => ({
      ...ev,
      affected_sectors: ev.affected_sectors || {},
      severity: ev.severity ?? 1,
      is_positive: isPositiveEvent(ev),
      treasury_injection: Number(ev.treasury_injection) || 0,
    }));

    const allocations = r.allocations || {};
    const revenues = r.revenues || {};
    const revenueFactors = r.revenue_factors || {};
    const consumptions = r.consumptions || {};

    const thresholds = deriveThresholds(r, sectorNames);
    const eventMultipliers =
      r.event_multipliers || aggregateEventMultipliers(events, sectorNames);

    const totalAllocation =
      r.total_allocation ??
      sectorNames.reduce((s, n) => s + (Number(allocations[n]) || 0), 0);
    const totalRevenue =
      r.total_revenue ??
      sectorNames.reduce((s, n) => s + (Number(revenues[n]) || 0), 0);
    const surplusReturned =
      r.surplus_returned ??
      sectorNames.reduce(
        (s, n) =>
          s + Math.max(0, (Number(allocations[n]) || 0) - (Number(consumptions[n]) || 0)),
        0,
      );

    const treasuryAfter = r.treasury_after ?? r.treasury ?? prevTreasuryAfter;
    const treasuryBefore = r.treasury_before ?? prevTreasuryAfter;
    prevTreasuryAfter = treasuryAfter;

    const treasuryInjection =
      r.treasury_injection ??
      events.reduce((s, e) => s + (Number(e.treasury_injection) || 0), 0);

    const population = Number(r.population) || 0;
    const productivity = Number(r.productivity) || 1;

    const avgRf =
      r.avg_revenue_factor ??
      average(sectorNames.map(n => Number(revenueFactors[n]) || 0));

    const prosperity =
      r.prosperity ?? (population > 0 ? totalRevenue / population : 0);

    const reward = r.reward || {};
    const total = Number(reward.total ?? 0);
    cum += total;
    const cumulative = r.cumulative_reward ?? cum;

    const isCriticalFailure = Boolean(
      r.done &&
        typeof r.termination_reason === 'string' &&
        r.termination_reason.startsWith('CRITICAL_FAILURE'),
    );
    const failingSectors = isCriticalFailure
      ? findFailingSectors(allocations, thresholds, sectorNames)
      : [];

    const roundNum = r.round_num ?? i + 1;
    return {
      round_num: roundNum,
      year: r.year ?? Math.floor((roundNum - 1) / 4) + 1,
      quarter: r.quarter ?? ((roundNum - 1) % 4) + 1,

      events,
      crisis_occurred: r.crisis_occurred ?? events.some(e => (e.severity || 0) >= 4),
      treasury_injection: treasuryInjection,

      debate: r.debate || [],
      proposal_order: r.proposal_order || sectorNames,
      proposals: r.proposals || [],
      votes: r.votes || [],
      vote_results: r.vote_results || [],

      allocations,
      consumptions,
      revenues,
      revenue_factors: revenueFactors,
      thresholds,
      event_multipliers: eventMultipliers,

      treasury_before: treasuryBefore,
      treasury_after: treasuryAfter,
      total_allocation: totalAllocation,
      total_revenue: totalRevenue,
      surplus_returned: surplusReturned,
      population,
      productivity,
      avg_revenue_factor: avgRf,
      prosperity,

      reward: {
        base_reward: Number(reward.base_reward) || 0,
        productivity_bonus: Number(reward.productivity_bonus) || 0,
        survival_bonus: Number(reward.survival_bonus) || 0,
        over_alloc_penalty: Number(reward.over_alloc_penalty) || 0,
        under_alloc_penalty: Number(reward.under_alloc_penalty) || 0,
        critical_penalty: Number(reward.critical_penalty) || 0,
        total,
      },
      cumulative_reward: cumulative,

      done: Boolean(r.done),
      termination_reason: r.termination_reason ?? null,
      is_critical_failure: isCriticalFailure,
      failing_sectors: failingSectors,
    };
  });

  const last = rounds[rounds.length - 1];
  const finalProsperity =
    (last.treasury_after + last.total_revenue) / Math.max(last.population, 1);
  const summary = raw.summary || {
    rounds_survived: last.round_num,
    total_reward: cum,
    final_treasury: last.treasury_after,
    final_prosperity: finalProsperity,
    final_productivity: last.productivity,
    final_population: last.population,
    termination_reason: last.termination_reason,
  };

  return {
    ...raw,
    config: {
      ...raw.config,
      sectors,
    },
    rounds,
    summary,
  };
}
