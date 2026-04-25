import { useState, useMemo } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from 'recharts';

const SERIES = {
  treasury: { label: 'Treasury', accessor: r => r.treasury_after, color: '#7c5cff' },
  total_revenue: { label: 'Revenue', accessor: r => r.total_revenue, color: '#2dd4bf' },
  productivity: { label: 'Productivity', accessor: r => r.productivity, color: '#f6c177' },
  prosperity: { label: 'Prosperity ×1e3', accessor: r => r.prosperity * 1000, color: '#60a5fa' },
  population: { label: 'Population', accessor: r => r.population, color: '#fb923c' },
  reward_total: { label: 'Reward (step)', accessor: r => r.reward.total, color: '#4ade80' },
  cumulative_reward: { label: 'Cumulative reward', accessor: r => r.cumulative_reward, color: '#f472b6' },
  total_allocation: { label: 'Total allocation', accessor: r => r.total_allocation, color: '#a78bfa' },
};

export default function TimeSeries({ rounds, currentRound }) {
  const [active, setActive] = useState(['treasury', 'total_revenue', 'cumulative_reward']);

  const data = useMemo(() => rounds.map(r => {
    const row = { round: r.round_num };
    for (const [k, s] of Object.entries(SERIES)) {
      row[k] = s.accessor(r);
    }
    return row;
  }), [rounds]);

  const toggle = key => {
    setActive(prev => (prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]));
  };

  return (
    <div className="card">
      <h3>
        Time series
        <span className="meta">{rounds.length} rounds</span>
      </h3>
      <div className="chart-tabs">
        {Object.entries(SERIES).map(([k, s]) => (
          <button
            key={k}
            type="button"
            className={active.includes(k) ? 'active' : ''}
            onClick={() => toggle(k)}
            style={{ color: active.includes(k) ? s.color : undefined }}
          >
            {s.label}
          </button>
        ))}
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
            <CartesianGrid stroke="#1d2230" strokeDasharray="3 3" />
            <XAxis dataKey="round" stroke="#5a6480" tick={{ fontSize: 11 }} />
            <YAxis stroke="#5a6480" tick={{ fontSize: 11 }} width={50} />
            <Tooltip
              contentStyle={{
                background: '#11141c',
                border: '1px solid #232838',
                borderRadius: 8,
                fontSize: 12,
              }}
              labelStyle={{ color: '#cbd2e0' }}
            />
            <ReferenceLine x={currentRound} stroke="#7c5cff" strokeDasharray="2 4" />
            {active.map(k => (
              <Line
                key={k}
                type="monotone"
                dataKey={k}
                stroke={SERIES[k].color}
                dot={false}
                strokeWidth={1.6}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
