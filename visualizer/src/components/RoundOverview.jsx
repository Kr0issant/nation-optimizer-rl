import { fmt, fmtSigned } from '../utils/format.js';

function Stat({ label, value, delta, deltaDir, hint }) {
  return (
    <div className="stat">
      <span className="label">{label}</span>
      <span className="value">{value}</span>
      {delta !== undefined && delta !== null && (
        <span className={`delta ${deltaDir || ''}`}>{delta}</span>
      )}
      {hint && <span className="hint">{hint}</span>}
    </div>
  );
}

function deltaArrow(curr, prev) {
  if (prev === undefined || prev === null) return { delta: undefined };
  const d = curr - prev;
  if (Math.abs(d) < 1e-6) return { delta: '·', dir: '' };
  return { delta: fmtSigned(d, Math.abs(d) < 1 ? 3 : 1), dir: d > 0 ? 'up' : 'down' };
}

export default function RoundOverview({ round, prevRound, summary }) {
  if (!round) return null;

  const treasuryDelta = deltaArrow(round.treasury_after, prevRound?.treasury_after);
  const prodDelta = deltaArrow(round.productivity, prevRound?.productivity);
  const popDelta = deltaArrow(round.population, prevRound?.population);
  const revDelta = deltaArrow(round.total_revenue, prevRound?.total_revenue);

  const treasuryHint = round.is_critical_failure
    ? 'frozen — failure before debit'
    : undefined;

  return (
    <div className="card">
      <h3>
        Round {round.round_num}
        <span className="meta">Y{round.year} · Q{round.quarter}</span>
      </h3>
      <div className="body">
        <div className="stat-grid">
          <Stat
            label="Treasury"
            value={fmt(round.treasury_after)}
            delta={treasuryDelta.delta}
            deltaDir={treasuryDelta.dir}
            hint={treasuryHint}
          />
          <Stat
            label="Total revenue"
            value={fmt(round.total_revenue)}
            delta={revDelta.delta}
            deltaDir={revDelta.dir}
          />
          <Stat
            label="Productivity"
            value={round.productivity.toFixed(3)}
            delta={prodDelta.delta}
            deltaDir={prodDelta.dir}
          />
          <Stat
            label="Population"
            value={fmt(round.population)}
            delta={popDelta.delta}
            deltaDir={popDelta.dir}
          />
          <Stat label="Allocations" value={fmt(round.total_allocation)} />
          <Stat label="Surplus returned" value={fmt(round.surplus_returned)} />
          <Stat label="Avg revenue ×" value={round.avg_revenue_factor.toFixed(2)} />
          <Stat label="Prosperity" value={(round.prosperity * 1000).toFixed(3) + ' /1k'} />
        </div>

        <div
          style={{
            borderTop: '1px solid var(--border)',
            paddingTop: 10,
            fontSize: 12,
            color: 'var(--text-dim)',
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 6,
          }}
        >
          <div>Cumulative reward (so far)</div>
          <div style={{ textAlign: 'right', color: 'var(--text-hi)', fontFamily: 'var(--mono)' }}>
            {fmtSigned(round.cumulative_reward, 1)}
          </div>
          {round.done && summary && (
            <>
              <div>Final prosperity</div>
              <div style={{ textAlign: 'right', color: 'var(--text-hi)', fontFamily: 'var(--mono)' }}>
                {(summary.final_prosperity * 1000).toFixed(3)} /1k
              </div>
              <div>Termination</div>
              <div style={{ textAlign: 'right', color: 'var(--text-hi)', fontFamily: 'var(--mono)' }}>
                {summary.termination_reason}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
