import { fmtSigned } from '../utils/format.js';

const COMPONENTS = [
  { key: 'base_reward', label: 'Base (prosperity)' },
  { key: 'productivity_bonus', label: 'Productivity bonus' },
  { key: 'survival_bonus', label: 'Survival bonus' },
  { key: 'over_alloc_penalty', label: 'Over-alloc penalty' },
  { key: 'under_alloc_penalty', label: 'Under-alloc penalty' },
  { key: 'critical_penalty', label: 'Critical penalty' },
];

export default function RewardCard({ reward, cumulative }) {
  if (!reward) return null;

  const max = Math.max(
    1,
    ...COMPONENTS.map(c => Math.abs(reward[c.key] || 0)),
  );

  return (
    <div className="card">
      <h3>
        Reward breakdown
        <span className="meta">cum {fmtSigned(cumulative, 1)}</span>
      </h3>
      <div className="body">
        {COMPONENTS.map(({ key, label }) => {
          const v = reward[key] || 0;
          const pct = (Math.abs(v) / max) * 50;
          return (
            <div className="reward-row" key={key}>
              <span className="rname">{label}</span>
              <div className="rbar">
                {v >= 0 ? (
                  <div className="pos" style={{ width: `${pct}%` }} />
                ) : (
                  <div className="neg" style={{ width: `${pct}%` }} />
                )}
              </div>
              <span className="rval" style={{ color: v < 0 ? 'var(--accent-bad)' : v > 0 ? 'var(--accent-good)' : 'var(--text-dim)' }}>
                {fmtSigned(v, 2)}
              </span>
            </div>
          );
        })}
        <div className="reward-total">
          <span>Step total</span>
          <span style={{ color: reward.total < 0 ? 'var(--accent-bad)' : 'var(--accent-good)' }}>
            {fmtSigned(reward.total, 2)}
          </span>
        </div>
      </div>
    </div>
  );
}
