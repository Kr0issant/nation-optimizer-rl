import clsx from 'clsx';
import { fmt, fmtPct } from '../utils/format.js';

const ZONE_COLORS = {
  CRITICAL: 'var(--zone-critical)',
  UNDERFUNDED: 'var(--zone-under)',
  PROFIT: 'var(--zone-profit)',
  WASTAGE: 'var(--zone-wastage)',
  ZERO: 'var(--text-mute)',
};

function zoneFor(allocation, t) {
  if (allocation === 0) return 'ZERO';
  if (allocation < t.critical) return 'CRITICAL';
  if (allocation < t.demand) return 'UNDERFUNDED';
  if (allocation <= t.surplus) return 'PROFIT';
  return 'WASTAGE';
}

export default function SectorCard({
  sector,
  allocation,
  revenue,
  revenueFactor,
  consumption,
  thresholds,
  eventMultiplier,
  isFailureRound = false,
  isFailingSector = false,
}) {
  const zone = zoneFor(allocation, thresholds);
  const zoneColor = ZONE_COLORS[zone];

  const max = Math.max(thresholds.wastage * 1.2, allocation * 1.05, 1);
  const allocPct = (allocation / max) * 100;
  const critPct = (thresholds.critical / max) * 100;
  const demandPct = (thresholds.demand / max) * 100;
  const surplusPct = (thresholds.surplus / max) * 100;
  const wastagePct = (thresholds.wastage / max) * 100;

  const ratio = thresholds.demand > 0 ? allocation / thresholds.demand : 0;

  return (
    <div
      className={clsx('sector', {
        'is-failure-round': isFailureRound,
        'is-failing-sector': isFailingSector,
      })}
      style={{ '--zone-color': zoneColor }}
    >
      <div className="head">
        <div>
          <span className="name">{sector.full_name}</span>
          {' '}<span className="full">{eventMultiplier !== 1 ? `event ×${eventMultiplier.toFixed(2)}` : ''}</span>
        </div>
        {isFailingSector ? (
          <span className="zone-badge failing">FAILED · {fmtPct(ratio)}</span>
        ) : isFailureRound ? (
          <span className="zone-badge muted">{zone} · no rev</span>
        ) : (
          <span className="zone-badge">{zone}</span>
        )}
      </div>

      <div className="alloc-bar" title={`Allocation ${fmt(allocation)} | Demand ${fmt(thresholds.demand)} | Surplus ${fmt(thresholds.surplus)}`}>
        <div className="zones">
          <div className="seg" style={{ width: `${critPct}%`, background: 'var(--zone-critical)' }} />
          <div className="seg" style={{ width: `${demandPct - critPct}%`, background: 'var(--zone-under)' }} />
          <div className="seg" style={{ width: `${surplusPct - demandPct}%`, background: 'var(--zone-profit)' }} />
          <div className="seg" style={{ width: `${wastagePct - surplusPct}%`, background: 'var(--zone-wastage)' }} />
          <div className="seg" style={{ width: `${100 - wastagePct}%`, background: 'var(--zone-wastage)', opacity: 0.08 }} />
        </div>
        <div className="alloc-fill" style={{ width: `${Math.min(allocPct, 100)}%` }} />
        <div className="marker" style={{ left: `${critPct}%` }}>
          <span className="label">crit</span>
        </div>
        <div className="marker" style={{ left: `${demandPct}%` }}>
          <span className="label">demand</span>
        </div>
        <div className="marker" style={{ left: `${surplusPct}%` }}>
          <span className="label">surplus</span>
        </div>
        <div className="marker" style={{ left: `${wastagePct}%` }}>
          <span className="label">wastage</span>
        </div>
      </div>

      <div className="metrics">
        <div className="m">
          <span className="l">Allocated</span>
          <span className="v">{fmt(allocation)}</span>
        </div>
        <div className="m">
          <span className="l">Revenue</span>
          <span className="v">{fmt(revenue)}</span>
        </div>
        <div className="m">
          <span className="l">RF × Prod</span>
          <span className="v">{revenueFactor.toFixed(2)}</span>
        </div>
        <div className="m">
          <span className="l">Demand</span>
          <span className="v">{fmt(thresholds.demand)}</span>
        </div>
        <div className="m">
          <span className="l">Consumed</span>
          <span className="v">{fmt(consumption)}</span>
        </div>
        <div className="m">
          <span className="l">% of demand</span>
          <span className="v">{fmtPct(ratio)}</span>
        </div>
      </div>
    </div>
  );
}
