import { useEffect, useMemo, useRef, useState } from 'react';
import clsx from 'clsx';
import './App.css';
import { sampleEpisode } from './sampleRun.js';
import { normalizeEpisode } from './utils/normalizeEpisode.js';
import RoundOverview from './components/RoundOverview.jsx';
import SectorCard from './components/SectorCard.jsx';
import PhasePanel from './components/PhasePanel.jsx';
import RewardCard from './components/RewardCard.jsx';
import TimeSeries from './components/TimeSeries.jsx';

const SPEEDS = [0.5, 1, 2, 4, 8];

function termPillClass(reason) {
  if (!reason) return 'neutral';
  if (reason.includes('PROSPERITY')) return 'success';
  if (reason.includes('MAX_ROUNDS')) return 'neutral';
  return 'failure';
}

const NORMALIZED_SAMPLE = normalizeEpisode(sampleEpisode);

export default function App() {
  const [episode, setEpisode] = useState(NORMALIZED_SAMPLE);
  const [roundIdx, setRoundIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const fileInputRef = useRef(null);

  const rounds = episode.rounds;
  const current = rounds[roundIdx];
  const prev = roundIdx > 0 ? rounds[roundIdx - 1] : null;
  const sectorMap = useMemo(
    () => Object.fromEntries(episode.config.sectors.map(s => [s.name, s])),
    [episode],
  );

  useEffect(() => {
    if (!playing) return undefined;
    const interval = 1100 / speed;
    const id = setInterval(() => {
      setRoundIdx(idx => {
        if (idx >= rounds.length - 1) {
          setPlaying(false);
          return idx;
        }
        return idx + 1;
      });
    }, interval);
    return () => clearInterval(id);
  }, [playing, speed, rounds.length]);

  useEffect(() => {
    setRoundIdx(0);
  }, [episode]);

  function onLoadFile(file) {
    const reader = new FileReader();
    reader.onload = e => {
      try {
        const parsed = JSON.parse(e.target.result);
        if (!parsed.rounds || !Array.isArray(parsed.rounds)) {
          alert('Invalid episode file: missing "rounds" array');
          return;
        }
        if (!parsed.config?.sectors) {
          alert('Invalid episode file: missing "config.sectors"');
          return;
        }
        setEpisode(normalizeEpisode(parsed));
      } catch (err) {
        alert(`Failed to parse episode JSON: ${err.message}`);
      }
    };
    reader.readAsText(file);
  }

  function onDrop(e) {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) onLoadFile(file);
  }

  return (
    <div className="app" onDragOver={e => e.preventDefault()} onDrop={onDrop}>
      <header className="topbar">
        <div className="brand">
          <span className="dot" />
          <span>Parliament RL · Episode Viewer</span>
        </div>
        <div className="episode-meta">
          <span>policy <b>{episode.policy || 'unknown'}</b></span>
          <span>seed <b>{episode.seed ?? '—'}</b></span>
          <span>id <b>{episode.episode_id || '—'}</b></span>
          <span>rounds <b>{rounds.length}</b></span>
        </div>
        <div className="spacer" />
        <div className="actions">
          <button onClick={() => fileInputRef.current?.click()} title="Load an episode JSON exported by evaluation/export_episode.py">
            Load episode JSON
          </button>
          <button
            className="primary"
            onClick={() => {
              setEpisode(NORMALIZED_SAMPLE);
              setRoundIdx(0);
            }}
          >
            Reset sample
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json"
            style={{ display: 'none' }}
            onChange={e => e.target.files?.[0] && onLoadFile(e.target.files[0])}
          />
        </div>
      </header>

      <div className="playback">
        <div className="round-label">
          Round <b style={{ color: 'var(--text-hi)' }}>{current.round_num}</b> / {rounds.length}
          <span className="muted">Y{current.year} · Q{current.quarter}</span>
        </div>
        <input
          type="range"
          min={0}
          max={rounds.length - 1}
          value={roundIdx}
          onChange={e => setRoundIdx(Number(e.target.value))}
        />
        <button
          className="primary"
          onClick={() => setPlaying(p => !p)}
          disabled={roundIdx >= rounds.length - 1 && !playing}
        >
          {playing ? 'Pause' : roundIdx >= rounds.length - 1 ? 'End' : 'Play'}
        </button>
        <div className="speed">
          <span>speed</span>
          <select value={speed} onChange={e => setSpeed(Number(e.target.value))}>
            {SPEEDS.map(s => (
              <option key={s} value={s}>{s}×</option>
            ))}
          </select>
          <span
            className={clsx('term-pill', termPillClass(current.termination_reason))}
            title={current.done ? 'Episode terminated' : 'In progress'}
          >
            {current.done ? current.termination_reason : 'in progress'}
          </span>
        </div>
      </div>

      <div className="layout">
        <div className="column">
          <RoundOverview round={current} prevRound={prev} summary={episode.summary} />
          <RewardCard reward={current.reward} cumulative={current.cumulative_reward} />
        </div>

        <div className="column">
          <div className="card">
            <h3>
              Sectors
              <span className="meta">
                allocation vs critical · demand · surplus · wastage
              </span>
            </h3>
            {current.is_critical_failure && (
              <div className="failure-banner">
                <strong>Critical failure:</strong>{' '}
                {current.failing_sectors.length > 0
                  ? `${current.failing_sectors.join(', ')} dropped below 40% of demand. `
                  : 'a sector dropped below 40% of demand. '}
                Treasury was not debited (the round terminates before allocation
                in Phase 5), so revenues for every sector are zero.
              </div>
            )}
            <div className="sector-grid">
              {episode.config.sectors.map(s => (
                <SectorCard
                  key={s.name}
                  sector={sectorMap[s.name]}
                  allocation={current.allocations[s.name] || 0}
                  revenue={current.revenues[s.name] || 0}
                  revenueFactor={current.revenue_factors[s.name] || 0}
                  consumption={current.consumptions[s.name] || 0}
                  thresholds={current.thresholds[s.name]}
                  eventMultiplier={current.event_multipliers[s.name] || 1}
                  isFailureRound={current.is_critical_failure}
                  isFailingSector={current.failing_sectors.includes(s.name)}
                />
              ))}
            </div>
          </div>

          <TimeSeries rounds={rounds} currentRound={current.round_num} />
        </div>

        <div className="column">
          <div className="card">
            <h3>
              Round {current.round_num} decisions
              <span className="meta">events → debate → vote</span>
            </h3>
            <PhasePanel round={current} />
          </div>
        </div>
      </div>

      {rounds.length === 1 && (
        <div className="dropzone">
          Drag and drop an <strong>episode.json</strong> here, or use{' '}
          <span className="kbd">Load episode JSON</span> above. Without a real episode
          the viewer is showing the synthetic sample run defined in{' '}
          <span className="kbd">src/sampleRun.js</span>.
        </div>
      )}
    </div>
  );
}
